"""Low-level Kafka utilities for administration, producing, and consuming."""

from __future__ import annotations

import time
import uuid
from typing import Any

from confluent_kafka import Consumer, KafkaError, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from google.protobuf.message import Message


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

    new_topics = [
        NewTopic(topic, num_partitions=num_partitions, replication_factor=replication_factor)
    ]
    fs = admin.create_topics(new_topics, request_timeout=timeout)
    for f in fs.values():
        try:
            f.result()
        except Exception as e:
            # Topic might have been created concurrently
            if "TOPIC_ALREADY_EXISTS" not in str(e):
                raise


class KafkaProtoReader:
    """Consumes protobuf messages from the earliest offset with an isolated consumer group."""

    def __init__(self, broker_addr: str, topic: str, group_id: str | None = None) -> None:
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

    def read_next_proto[T: Message](self, proto_cls: type[T], timeout: float = 15.0) -> T:
        """Reads the next message and deserializes it into the specified Protobuf class."""
        val = self.read_next(timeout)
        msg = proto_cls()
        msg.ParseFromString(val)
        return msg

    def close(self) -> None:
        self.consumer.close()


def publish_proto(
    broker_addr: str,
    topic: str,
    message: Message,
    key: str | bytes | None = None,
    timeout: float = 10.0,
) -> None:
    """Serializes and produces a Protobuf message to the specified topic."""
    producer = Producer({"bootstrap.servers": broker_addr})
    if key is None:
        key_bytes = b""
    elif isinstance(key, str):
        key_bytes = key.encode("utf-8")
    else:
        key_bytes = key
    val = message.SerializeToString()

    delivery_err: Exception | None = None

    def on_delivery(err: Any, msg: Any) -> None:
        nonlocal delivery_err
        if err:
            delivery_err = RuntimeError(f"Delivery failed: {err}")

    producer.produce(topic=topic, key=key_bytes, value=val, callback=on_delivery)
    producer.flush(timeout=timeout)
    if delivery_err:
        raise delivery_err
