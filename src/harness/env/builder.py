"""Fluent builder for creating and orchestrating ephemeral integration test environments."""

from __future__ import annotations

import io
import logging
import os
import socket
import tarfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from harness.config import Config, load_config
from harness.env.environment import TestEnvironment
from harness.env.podman import get_docker_client
from harness.env.prune import default_labels
from harness.testutil.db import connect_mysql
from harness.testutil.kafka import ensure_topic
from harness.testutil.mock_aaa import setup_wiremock_aaa
from harness.testutil.redis import connect_redis

logger = logging.getLogger(__name__)


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 60.0) -> None:
    """Blocks until a TCP port is open and accepting connections on host."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except (OSError, ConnectionRefusedError):
            time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for port {host}:{port} after {timeout}s")


@dataclass
class DatabaseMigration:
    database: str
    migration_dir: str


@dataclass
class MySQLConfig:
    databases: List[str] = field(default_factory=list)
    check_tables: List[str] = field(default_factory=list)
    migrations: List[DatabaseMigration] = field(default_factory=list)


@dataclass
class KafkaConfig:
    topics: List[str] = field(default_factory=list)


class EnvironmentBuilder:
    """Builder pattern for provisioning isolated containers on a dedicated bridge network."""

    def __init__(self, network_name: str) -> None:
        self.network_name = network_name
        self.mysql_config: Optional[MySQLConfig] = None
        self.redis_aliases: List[str] = []
        self.shared_redis: bool = False
        self.kafka_config: Optional[KafkaConfig] = None
        self.enable_wiremock: bool = False
        self.config: Optional[Config] = None

    def with_config(self, cfg: Config) -> EnvironmentBuilder:
        self.config = cfg
        return self

    def with_mysql(
        self,
        databases: List[str],
        check_tables: Optional[List[str]] = None,
        migrations: Optional[List[DatabaseMigration]] = None,
    ) -> EnvironmentBuilder:
        self.mysql_config = MySQLConfig(
            databases=databases,
            check_tables=check_tables or [],
            migrations=migrations or [],
        )
        return self

    def with_redis(self, *aliases: str) -> EnvironmentBuilder:
        for a in aliases:
            if a not in self.redis_aliases:
                self.redis_aliases.append(a)
        return self

    def with_redis_instance(self, alias: str) -> EnvironmentBuilder:
        return self.with_redis(alias)

    def with_shared_redis(self, *aliases: str) -> EnvironmentBuilder:
        """Provision one Redis server reachable through all supplied aliases."""
        self.shared_redis = True
        return self.with_redis(*aliases)

    def with_kafka(self, topics: List[str]) -> EnvironmentBuilder:
        self.kafka_config = KafkaConfig(topics=topics)
        return self

    def with_wiremock(self) -> EnvironmentBuilder:
        self.enable_wiremock = True
        return self

    def build(self) -> TestEnvironment:
        cfg = self.config or load_config()
        client = get_docker_client()
        env = TestEnvironment(client=client)

        try:
            # 1. Create isolated bridge network (clean up existing one if leftover from previous run)
            try:
                existing_net = client.networks.get(self.network_name)
                existing_net.remove()
            except Exception:
                pass

            net = client.networks.create(
                self.network_name,
                driver="bridge",
                labels=default_labels("network"),
            )
            env.network = net

            # 2. MySQL Container (if requested)
            if self.mysql_config:
                initial_db = self.mysql_config.databases[0] if self.mysql_config.databases else "test"
                mysql_image = cfg.get_image("mysql", "mysql:8.0")

                mysql_endpoint_config = {
                    net.name: client.api.create_endpoint_config(aliases=["mysql"])
                }
                mysql_c = client.containers.run(
                    image=mysql_image,
                    detach=True,
                    environment={
                        "MYSQL_ROOT_PASSWORD": "root",
                        "MYSQL_DATABASE": initial_db,
                    },
                    ports={"3306/tcp": None},
                    labels=default_labels("mysql"),
                    network=net.name,
                    networking_config=mysql_endpoint_config,
                )
                env.mysql_container = mysql_c

                mysql_c.reload()
                mapped_port = int(mysql_c.attrs["NetworkSettings"]["Ports"]["3306/tcp"][0]["HostPort"])
                env.mysql_host_dsn = f"root:root@tcp(127.0.0.1:{mapped_port})/{initial_db}"

                wait_for_port(mapped_port, timeout=120.0)
                env.db = connect_mysql(env.mysql_host_dsn, timeout=120.0)

                # Ensure requested databases exist
                with env.db.cursor() as cursor:
                    for db_name in self.mysql_config.databases:
                        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")

                # Run Flyway migrations
                migrations = list(self.mysql_config.migrations)
                if not migrations:
                    for db_name in self.mysql_config.databases:
                        svc_name = db_name.replace("_", "-")
                        repo_dir = cfg.get_local_repo_dir(svc_name)
                        cand = Path(repo_dir) / "resources" / "db" / "migration"
                        if cand.is_dir():
                            migrations.append(DatabaseMigration(database=db_name, migration_dir=str(cand.resolve())))

                for mig in migrations:
                    if mig.migration_dir:
                        self._run_flyway_migration(cfg, client, net, "mysql", "3306", mig.database, mig.migration_dir)

            # 3. Redis Instances (if requested)
            redis_image = cfg.get_image("redis", "redis:7-alpine")
            redis_alias_groups = [self.redis_aliases] if self.shared_redis else [[a] for a in self.redis_aliases]
            for aliases in redis_alias_groups:
                if not aliases:
                    continue
                primary_alias = aliases[0]
                redis_endpoint_config = {
                    net.name: client.api.create_endpoint_config(aliases=aliases)
                }
                rc = client.containers.run(
                    image=redis_image,
                    detach=True,
                    ports={"6379/tcp": None},
                    labels=default_labels(primary_alias),
                    network=net.name,
                    networking_config=redis_endpoint_config,
                )
                for alias in aliases:
                    env.redis_containers[alias] = rc

                rc.reload()
                rport = int(rc.attrs["NetworkSettings"]["Ports"]["6379/tcp"][0]["HostPort"])
                addr = f"127.0.0.1:{rport}"
                wait_for_port(rport, timeout=60.0)
                redis_client = connect_redis(addr, timeout=60.0)
                for alias in aliases:
                    env.redis_addrs[alias] = addr
                    env.redis_clients[alias] = redis_client

            # 4. Kafka Broker (if requested)
            if self.kafka_config:
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

                for topic in self.kafka_config.topics:
                    ensure_topic(env.kafka_broker_addr, topic, timeout=60.0)

            # 5. WireMock (if requested)
            if self.enable_wiremock:
                wm_image = cfg.get_image("wiremock", "docker.io/wiremock/wiremock:3.5.2")
                wm_endpoint_config = {
                    net.name: client.api.create_endpoint_config(aliases=["mock-services"])
                }
                wm_c = client.containers.run(
                    image=wm_image,
                    detach=True,
                    ports={"8080/tcp": None},
                    labels=default_labels("wiremock"),
                    network=net.name,
                    networking_config=wm_endpoint_config,
                )
                env.wiremock_container = wm_c

                wm_c.reload()
                wm_port = int(wm_c.attrs["NetworkSettings"]["Ports"]["8080/tcp"][0]["HostPort"])
                env.wiremock_host_url = f"http://127.0.0.1:{wm_port}"

                wait_for_port(wm_port, timeout=60.0)
                setup_wiremock_aaa(env.wiremock_host_url)

            return env

        except Exception:
            env.teardown()
            raise

    def _run_flyway_migration(
        self,
        cfg: Config,
        client,
        net,
        db_host: str,
        db_port: str,
        database: str,
        migration_dir: str,
    ) -> None:
        """Runs ephemeral Flyway container against the target database on the bridge network."""
        flyway_image = cfg.get_image("flyway", "docker.io/flyway/flyway:11-alpine")
        jdbc_url = f"jdbc:mysql://{db_host}:{db_port}/{database}?connectTimeout=30000"

        volumes = {
            os.path.abspath(migration_dir): {
                "bind": "/flyway/sql",
                "mode": "ro",
            }
        }

        command = [
            f"-url={jdbc_url}",
            "-user=root",
            "-password=root",
            "-connectRetries=10",
            "migrate",
        ]

        logger.info(f"Running Flyway migration for database '{database}' from '{migration_dir}'")
        flyway_c = client.containers.run(
            image=flyway_image,
            command=command,
            volumes=volumes,
            network=net.name,
            detach=False,
            remove=True,
            labels=default_labels(f"flyway-{database}"),
        )
