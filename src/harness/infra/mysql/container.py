"""MySQL container lifecycle management and initialization."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from harness.env.prune import default_labels
from harness.infra.mysql.flyway import run_flyway_migration
from harness.infra.mysql.util import connect_mysql
from harness.infra.wait import wait_for_port

if TYPE_CHECKING:
    from harness.config import Config
    from harness.env.environment import TestEnvironment

logger = logging.getLogger(__name__)


@dataclass
class DatabaseMigration:
    database: str
    migration_dir: str


@dataclass
class MySQLConfig:
    databases: list[str] = field(default_factory=list)
    check_tables: list[str] = field(default_factory=list)
    migrations: list[DatabaseMigration] = field(default_factory=list)


def provision_mysql(
    client,
    net,
    cfg: Config,
    mysql_config: MySQLConfig,
    env: TestEnvironment,
) -> None:
    """Provisions a MySQL container on the bridge network and initializes databases and migrations."""
    initial_db = mysql_config.databases[0] if mysql_config.databases else "test"
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
        for db_name in mysql_config.databases:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")

    # Run Flyway migrations
    migrations = list(mysql_config.migrations)
    if not migrations:
        for db_name in mysql_config.databases:
            svc_name = db_name.replace("_", "-")
            repo_dir = cfg.get_local_repo_dir(svc_name)
            cand = Path(repo_dir) / "resources" / "db" / "migration"
            if cand.is_dir():
                migrations.append(DatabaseMigration(database=db_name, migration_dir=str(cand.resolve())))

    for mig in migrations:
        if mig.migration_dir:
            run_flyway_migration(cfg, client, net, "mysql", "3306", mig.database, mig.migration_dir)
