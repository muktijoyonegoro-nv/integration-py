"""Kafka KRaft broker container lifecycle and topic initialization."""

from __future__ import annotations

import io
import logging
import tarfile
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from harness.env.prune import default_labels
from harness.infra.kafka.util import ensure_topic
from harness.infra.wait import wait_for_port

if TYPE_CHECKING:
    from harness.config import Config
    from harness.env.environment import TestEnvironment

logger = logging.getLogger(__name__)


@dataclass
class KafkaConfig:
    topics: list[str] = field(default_factory=list)


def provision_kafka(
    client,
    net,
    cfg: Config,
    kafka_config: KafkaConfig,
    env: TestEnvironment,
) -> None:
    """Provisions a Confluent Kafka broker container in KRaft mode and ensures topics exist."""
    kafka_image = cfg.get_image("kafka", "confluentinc/confluent-local:7.6.0")

    starter_script_path = "/usr/sbin/testcontainers_start.sh"
    cmd = f"while [ ! -f {starter_script_path} ]; do sleep 0.1; done; bash {starter_script_path}"

    kafka_endpoint_config = {
        net.name: client.api.create_endpoint_config(aliases=["kafka"])
    }
    kafka_c = client.containers.run(
        image=kafka_image,
        entrypoint="sh",
        command=["-c", cmd],
        detach=True,
        ports={"9093/tcp": None},
        labels=default_labels("kafka"),
        network=net.name,
        networking_config=kafka_endpoint_config,
        environment={
            "KAFKA_LISTENERS": "PLAINTEXT://0.0.0.0:9093,BROKER://0.0.0.0:9092,CONTROLLER://0.0.0.0:9094",
            "KAFKA_REST_BOOTSTRAP_SERVERS": "PLAINTEXT://0.0.0.0:9093,BROKER://0.0.0.0:9092,CONTROLLER://0.0.0.0:9094",
            "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "BROKER:PLAINTEXT,PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT",
            "KAFKA_INTER_BROKER_LISTENER_NAME": "BROKER",
            "KAFKA_BROKER_ID": "1",
            "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": "1",
            "KAFKA_OFFSETS_TOPIC_NUM_PARTITIONS": "1",
            "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR": "1",
            "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR": "1",
            "KAFKA_LOG_FLUSH_INTERVAL_MESSAGES": "9223372036854775807",
            "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS": "0",
            "KAFKA_NODE_ID": "1",
            "KAFKA_PROCESS_ROLES": "broker,controller",
            "KAFKA_CONTROLLER_LISTENER_NAMES": "CONTROLLER",
            "KAFKA_CONTROLLER_QUORUM_VOTERS": "1@kafka:9094",
        },
    )
    env.kafka_container = kafka_c

    kafka_c.reload()
    kport = int(kafka_c.attrs["NetworkSettings"]["Ports"]["9093/tcp"][0]["HostPort"])
    env.kafka_broker_addr = f"127.0.0.1:{kport}"

    # Inject dynamic advertised listeners script with discovered host port
    script_lines = [
        "#!/bin/bash",
        'export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"',
        "source /etc/confluent/docker/bash-config",
        f'export KAFKA_ADVERTISED_LISTENERS="PLAINTEXT://127.0.0.1:{kport},BROKER://kafka:9092"',
        "echo Starting Kafka KRaft mode",
        "sed -i '/KAFKA_ZOOKEEPER_CONNECT/d' /etc/confluent/docker/configure",
        'echo "kafka-storage format --ignore-formatted -t 4L622nShTUiBen8AwTRapA -c /etc/kafka/kafka.properties" >> /etc/confluent/docker/configure',
        'echo "" > /etc/confluent/docker/ensure',
        "/etc/confluent/docker/configure",
        "/etc/confluent/docker/launch",
    ]
    script_content = "\n".join(script_lines) + "\n"

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        encoded = script_content.encode("utf-8")
        ti = tarfile.TarInfo(name="testcontainers_start.sh")
        ti.size = len(encoded)
        ti.mode = 0o755
        ti.mtime = int(time.time())
        tar.addfile(ti, io.BytesIO(encoded))
    tar_stream.seek(0)
    kafka_c.put_archive("/usr/sbin", tar_stream)

    wait_for_port(kport, timeout=120.0)

    for topic in kafka_config.topics:
        ensure_topic(env.kafka_broker_addr, topic, timeout=60.0)
