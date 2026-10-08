"""Reusable integration scenario harness orchestrating EnvironmentBuilder and ServiceCatalog."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from harness.catalog import SortMistake, SortService
from harness.catalog.service import AppContainer, ServiceDefinition, start_service
from harness.env.builder import DatabaseMigration, EnvironmentBuilder
from harness.env.environment import TestEnvironment
from harness.env.shared import SharedTestEnvironment
from tests.common.connectivity import assert_connectivity
from tests.common.schema import ScenarioConfig, load_scenario_config

logger = logging.getLogger(__name__)

SERVICE_CATALOG: Dict[str, ServiceDefinition] = {
    "sort-mistake": SortMistake,
    "sort-service": SortService,
}


@dataclass
class Scenario:
    """Represents an active test scenario instance with its environment and running services."""

    config: ScenarioConfig
    env: TestEnvironment
    apps: Dict[str, AppContainer] = field(default_factory=dict)
    shared_infra: Optional[SharedTestEnvironment] = None

    @property
    def db(self):
        return self.env.db

    @property
    def kafka_broker(self) -> str:
        return self.env.kafka_broker_addr

    @property
    def wiremock_url(self) -> str:
        return self.env.wiremock_host_url

    def redis_client(self, alias: str):
        return self.env.redis_clients.get(alias)

    def truncate_tables(self, tables: Optional[List[str]] = None) -> None:
        """Truncates tables in the scenario's MySQL database."""
        if self.db:
            from harness.testutil.db import truncate_tables
            truncate_tables(self.db, tables=tables)

    def flush_redis(self) -> None:
        """Flushes all redis client instances configured in this scenario."""
        flushed = set()
        for client in self.env.redis_clients.values():
            if id(client) in flushed:
                continue
            try:
                client.flushall()
                flushed.add(id(client))
            except Exception:
                pass

    def dump_logs(self) -> None:
        """Dumps logs from application and infrastructure containers upon test failure."""
        logger.warning(f"=== Scenario [{self.config.name}] Failure: Dumping Container Logs ===")
        for name, app in self.apps.items():
            try:
                logs = app.container.logs(tail=200).decode("utf-8", errors="replace")
                logger.warning(f"\n--- Logs for {name} ({app.container.name}) ---\n{logs}")
            except Exception as e:
                logger.warning(f"Failed to dump logs for {name}: {e}")

    def app(self, name: str) -> AppContainer:
        """Returns the running application container wrapper by service name."""
        if name not in self.apps:
            raise KeyError(f"Service '{name}' is not running in this scenario. Running: {list(self.apps.keys())}")
        return self.apps[name]

    def endpoint(self, name: str, port: str = "9000/tcp") -> str:
        """Returns the HTTP endpoint reachable from the host for the service."""
        return self.app(name).host_endpoint(port)

    def teardown(self) -> None:
        """Tears down all containers, networks, and connections."""
        if self.shared_infra is None:
            self.env.teardown()
            return

        for app in self.apps.values():
            try:
                app.container.remove(force=True, v=True)
            except Exception as exc:
                logger.warning("Error terminating app container: %s", exc)
            finally:
                if app.container in self.env.app_containers:
                    self.env.app_containers.remove(app.container)


def setup_scenario(
    config_path: Path | str,
    subtests: Optional[Any] = None,
    shared_infra: Optional[SharedTestEnvironment] = None,
) -> Scenario:
    """Parses a scenario config.yaml, sets up backing infrastructure, runs connectivity checks,

    and launches requested microservices.
    """
    cfg = load_scenario_config(config_path)
    if shared_infra is not None:
        shared_infra.prepare_scenario(cfg)
        env = shared_infra.env
    else:
        net_name = cfg.network_name or (cfg.name.replace("/", "-").replace("_", "-") + "-net")
        builder = EnvironmentBuilder(network_name=net_name)

        if cfg.mysql.databases:
            migrations = [
                DatabaseMigration(database=m.database, migration_dir=m.migration_dir)
                for m in cfg.mysql.migrations
            ]
            builder.with_mysql(
                databases=cfg.mysql.databases,
                check_tables=cfg.mysql.check_tables,
                migrations=migrations,
            )

        if cfg.kafka.topics:
            builder.with_kafka(topics=cfg.kafka.topics)

        for alias in cfg.redis_instances:
            builder.with_redis_instance(alias)

        if cfg.wiremock:
            builder.with_wiremock()

        env = builder.build()
    scenario = Scenario(config=cfg, env=env, shared_infra=shared_infra)

    try:
        # Launch application containers
        for svc_cfg in cfg.services:
            base_def = SERVICE_CATALOG.get(svc_cfg.name)
            if not base_def:
                raise ValueError(f"Unknown service '{svc_cfg.name}' in catalog")

            # Apply env overrides if any
            merged_env = dict(base_def.env)
            if svc_cfg.env_overrides:
                merged_env.update(svc_cfg.env_overrides)

            svc_def = ServiceDefinition(
                name=base_def.name,
                aliases=base_def.aliases,
                default_image=base_def.default_image,
                exposed_ports=base_def.exposed_ports,
                env=merged_env,
                health_path=base_def.health_path,
                readiness_timeout=base_def.readiness_timeout,
                startup_timeout=base_def.startup_timeout,
            )

            app = start_service(env, svc_def, image_override=svc_cfg.image_override or None)
            scenario.apps[svc_cfg.name] = app

        # Perform subtest connectivity assertions if requested
        if subtests is not None:
            assert_connectivity(s=scenario, subtests=subtests)

        return scenario

    except Exception:
        scenario.teardown()
        raise
