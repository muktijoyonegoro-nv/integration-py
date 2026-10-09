"""Fluent builder for creating and orchestrating ephemeral integration test environments."""

from __future__ import annotations

import contextlib
import logging

from harness.config import Config, load_config
from harness.env.environment import TestEnvironment
from harness.env.podman import get_docker_client
from harness.env.prune import default_labels
from harness.infra import (
    DatabaseMigration,
    KafkaConfig,
    MySQLConfig,
    provision_kafka,
    provision_mysql,
    provision_redis,
    provision_wiremock,
    wait_for_port,
)

logger = logging.getLogger(__name__)

# Re-export infra types for backwards compatibility
__all__ = [
    "DatabaseMigration",
    "EnvironmentBuilder",
    "KafkaConfig",
    "MySQLConfig",
    "wait_for_port",
]


class EnvironmentBuilder:
    """Builder pattern for provisioning isolated containers on a dedicated bridge network."""

    def __init__(self, network_name: str) -> None:
        self.network_name = network_name
        self.mysql_config: MySQLConfig | None = None
        self.redis_aliases: list[str] = []
        self.shared_redis: bool = False
        self.kafka_config: KafkaConfig | None = None
        self.enable_wiremock: bool = False
        self.config: Config | None = None

    def with_config(self, cfg: Config) -> EnvironmentBuilder:
        self.config = cfg
        return self

    def with_mysql(
        self,
        databases: list[str],
        check_tables: list[str] | None = None,
        migrations: list[DatabaseMigration] | None = None,
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

    def with_kafka(self, topics: list[str]) -> EnvironmentBuilder:
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
            with contextlib.suppress(Exception):
                existing_net = client.networks.get(self.network_name)
                existing_net.remove()

            net = client.networks.create(
                self.network_name,
                driver="bridge",
                labels=default_labels("network"),
            )
            env.network = net

            # 2. Provision MySQL Container & run Flyway migrations
            if self.mysql_config:
                provision_mysql(client, net, cfg, self.mysql_config, env)

            # 3. Provision Redis Instance(s)
            if self.redis_aliases:
                provision_redis(client, net, cfg, self.redis_aliases, self.shared_redis, env)

            # 4. Provision Kafka KRaft Broker & prepare topics
            if self.kafka_config:
                provision_kafka(client, net, cfg, self.kafka_config, env)

            # 5. Provision WireMock & seed base AAA mock
            if self.enable_wiremock:
                provision_wiremock(client, net, cfg, env)

            return env

        except Exception:
            env.teardown()
            raise
