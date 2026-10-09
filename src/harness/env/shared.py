"""Session-scoped shared infrastructure for integration scenarios."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable

import httpx
from confluent_kafka.admin import AdminClient

from harness.env.builder import DatabaseMigration, EnvironmentBuilder
from harness.env.environment import TestEnvironment
from harness.infra.kafka import ensure_topic
from harness.infra.mysql import connect_mysql
from harness.infra.wiremock import setup_wiremock_aaa

logger = logging.getLogger(__name__)


class SharedTestEnvironment:
    """Owns backing containers for one pytest session and resets their state per scenario."""

    def __init__(
        self, env: TestEnvironment, databases: set[str], topics: set[str], wiremock: bool
    ) -> None:
        self.env = env
        self.databases = databases
        self.topics = topics
        self.wiremock = wiremock

    @classmethod
    def start(cls, scenario_configs: Iterable[object]) -> SharedTestEnvironment:
        """Build shared infrastructure from the union of selected scenario configurations."""
        configs = list(scenario_configs)
        databases: set[str] = set()
        topics: set[str] = set()
        redis_aliases: set[str] = set()
        migrations: dict[str, str] = {}
        wiremock = False

        for cfg in configs:
            databases.update(cfg.mysql.databases)
            topics.update(cfg.kafka.topics)
            redis_aliases.update(cfg.redis_instances)
            wiremock = wiremock or cfg.wiremock
            for migration in cfg.mysql.migrations:
                if migration.migration_dir:
                    migrations.setdefault(migration.database, migration.migration_dir)

        builder = EnvironmentBuilder(network_name="integration-shared-net")
        if databases:
            builder.with_mysql(
                databases=sorted(databases),
                migrations=[
                    DatabaseMigration(database=db, migration_dir=path)
                    for db, path in migrations.items()
                ],
            )
        if topics:
            builder.with_kafka(sorted(topics))
        if redis_aliases:
            builder.with_shared_redis(*sorted(redis_aliases))
        if wiremock:
            builder.with_wiremock()

        return cls(builder.build(), databases, topics, wiremock)

    def prepare_scenario(self, cfg: object) -> None:
        """Restore all shared backing services to a clean state before a scenario starts."""
        self.reset_db()
        self.reset_redis()
        self.reset_kafka()
        self.reset_wiremock()

    def reset_db(self) -> None:
        """Truncate all base tables in every session database."""
        if not self.env.mysql_host_dsn:
            return

        for database in self.databases:
            dsn = self.env.mysql_host_dsn.rsplit("/", 1)[0] + f"/{database}"
            conn = connect_mysql(dsn)
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = %s AND table_type = 'BASE TABLE'",
                        (database,),
                    )
                    tables = [
                        row.get("table_name") or row["TABLE_NAME"] for row in cursor.fetchall()
                    ]
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                    try:
                        for table in tables:
                            safe_table = table.replace("`", "``")
                            safe_database = database.replace("`", "``")
                            cursor.execute(f"TRUNCATE TABLE `{safe_database}`.`{safe_table}`")
                    finally:
                        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            finally:
                conn.close()

    def reset_redis(self) -> None:
        """Flush each physical Redis instance once."""
        seen: set[int] = set()
        for client in self.env.redis_clients.values():
            if id(client) not in seen:
                client.flushall()
                seen.add(id(client))

    def reset_kafka(self) -> None:
        """Delete and recreate session topics so no records survive between scenarios."""
        if not self.env.kafka_broker_addr or not self.topics:
            return

        admin = AdminClient({"bootstrap.servers": self.env.kafka_broker_addr})
        metadata = admin.list_topics(timeout=10).topics
        existing = [
            topic for topic in self.topics if topic in metadata and metadata[topic].error is None
        ]
        if existing:
            futures = admin.delete_topics(existing, operation_timeout=30, request_timeout=30)
            for future in futures.values():
                future.result(30)

            deadline = time.time() + 30
            while time.time() < deadline:
                current = admin.list_topics(timeout=10).topics
                if not any(topic in current for topic in existing):
                    break
                time.sleep(0.2)
            else:
                raise TimeoutError(f"Kafka topics were not deleted in time: {existing}")

        for topic in self.topics:
            ensure_topic(self.env.kafka_broker_addr, topic, timeout=30)

    def reset_wiremock(self) -> None:
        """Clear mappings and request logs, then restore the global AAA stub."""
        if not self.wiremock or not self.env.wiremock_host_url:
            return
        base = self.env.wiremock_host_url.rstrip("/")
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{base}/__admin/reset")
            response.raise_for_status()
        setup_wiremock_aaa(base)

    def teardown(self) -> None:
        self.env.teardown()
