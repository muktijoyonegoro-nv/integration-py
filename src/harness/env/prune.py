"""Safe managed container pruning targeting label harness.managed=true."""

from __future__ import annotations

import logging
import os
from typing import Dict, List

import docker

from harness.env.podman import get_docker_client

LABEL_MANAGED = "harness.managed"
LABEL_SUITE = "harness.suite"
LABEL_SERVICE = "harness.service"
LABEL_RUN_ID = "harness.run_id"
MANAGED_VALUE = "true"
SUITE_VALUE = "integration-py"

logger = logging.getLogger(__name__)


def default_labels(service_name: str = "") -> Dict[str, str]:
    """Returns standard metadata labels attached to test containers."""
    labels = {
        LABEL_MANAGED: MANAGED_VALUE,
        LABEL_SUITE: SUITE_VALUE,
    }
    if service_name:
        labels[LABEL_SERVICE] = service_name
    if run_id := os.environ.get("HARNESS_RUN_ID"):
        labels[LABEL_RUN_ID] = run_id
    return labels


def prune_managed_containers(client: docker.DockerClient | None = None) -> List[str]:
    """Discovers and force-removes all containers labeled harness.managed=true.

    SAFETY GUARANTEE:
    This operation strictly prunes containers and associated anonymous volumes.
    It will NEVER prune, untag, delete, or modify any container images.

    Returns the list of pruned container IDs.
    """
    cli = client or get_docker_client()
    pruned: List[str] = []

    try:
        containers = cli.containers.list(
            all=True,
            filters={"label": f"{LABEL_MANAGED}={MANAGED_VALUE}"},
        )
        for container in containers:
            try:
                container.remove(force=True, v=True)
                pruned.append(container.id)
            except Exception as e:
                logger.warning("Failed removing managed container %s: %s", container.id, e)
    except Exception as e:
        logger.error("Failed querying containers for pruning: %s", e)

    return pruned
