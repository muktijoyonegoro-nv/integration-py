"""Low-level Kafka utilities for administration, producing, and consuming."""

from __future__ import annotations

import time
import uuid
from typing import Any, List, Optional

from confluent_kafka import Consumer, KafkaError, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from google.protobuf.message import Message

from proto.protos_sort.sortmistake import sort_node_pb2


def ensure_topic(
    broker_addr: str,
    topic: str,
    num_partitions: int = 1,
    replication_factor: int = 1,
    timeout: float = 30.0,
) -> None:
    """Creates a Kafka topic if it does not already exist."""
    admin = AdminClient({"bootstrap.servers": broker_addr})
    metadata = admin.list_topics(timeout=10.0)
    if topic in metadata.topics and metadata.topics[topic].error is None:
        return

    new_topics = [NewTopic(topic, num_partitions=num_partitions, replication_factor=replication_factor)]
    fs = admin.create_topics(new_topics, request_timeout=timeout)
    for t, f in fs.items():
        try:
            f.result()
        except Exception as e:
            # Topic might have been created concurrently
            if "TOPIC_ALREADY_EXISTS" not in str(e):
                raise


class KafkaProtoReader:
    """Consumes protobuf messages from the earliest offset with an isolated consumer group."""

    def __init__(self, broker_addr: str, topic: str, group_id: Optional[str] = None) -> None:
        self.broker_addr = broker_addr
        self.topic = topic
        self.group_id = group_id or f"test-group-{uuid.uuid4().hex[:8]}"
        self.consumer = Consumer({
            "bootstrap.servers": broker_addr,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })
        self.consumer.subscribe([topic])

    def read_next(self, timeout: float = 15.0) -> bytes:
        """Polls for the next message payload, raising TimeoutError if none arrived within timeout."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self.consumer.poll(0.5)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise RuntimeError(f"Kafka consumer error: {msg.error()}")
            return msg.value()
        raise TimeoutError(f"Timed out waiting for message on topic [{self.topic}] after {timeout}s")

    def read_next_sort_node_event(self, timeout: float = 15.0) -> sort_node_pb2.SortNodeEvents:
        """Reads the next message and deserializes it into SortNodeEvents."""
        val = self.read_next(timeout)
        events = sort_node_pb2.SortNodeEvents()
        events.ParseFromString(val)
        return events

    def close(self) -> None:
        self.consumer.close()


def publish_sort_node_events(
    broker_addr: str,
    topic: str,
    events: sort_node_pb2.SortNodeEvents,
    timeout: float = 10.0,
) -> None:
    """Serializes and produces a SortNodeEvents message to the specified topic."""
    producer = Producer({"bootstrap.servers": broker_addr})
    key = events.system_id.encode("utf-8") if events.system_id else b""
    val = events.SerializeToString()

    delivery_err: Optional[Exception] = None

    def on_delivery(err: Any, msg: Any) -> None:
        nonlocal delivery_err
        if err:
            delivery_err = RuntimeError(f"Delivery failed: {err}")

    producer.produce(topic=topic, key=key, value=val, callback=on_delivery)
    producer.flush(timeout=timeout)
    if delivery_err:
        raise delivery_err
