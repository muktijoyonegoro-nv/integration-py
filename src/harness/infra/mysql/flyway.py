"""Flyway migration container execution."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from harness.env.prune import default_labels

if TYPE_CHECKING:
    from harness.config import Config

logger = logging.getLogger(__name__)


def run_flyway_migration(
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
    client.containers.run(
        image=flyway_image,
        command=command,
        volumes=volumes,
        network=net.name,
        detach=False,
        remove=True,
        labels=default_labels(f"flyway-{database}"),
    )
