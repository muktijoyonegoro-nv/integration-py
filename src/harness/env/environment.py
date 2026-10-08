"""TestEnvironment runtime state and container manager."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import docker
import pymysql
import redis
from docker.models.containers import Container
from docker.models.networks import Network

from harness.env.podman import get_docker_client
from harness.env.prune import prune_managed_containers

logger = logging.getLogger(__name__)


class TestEnvironment:
    """Encapsulates active containers, networks, client pools, and host mapped endpoints."""

    def __init__(
        self,
        network: Optional[Network] = None,
        client: Optional[docker.DockerClient] = None,
    ) -> None:
        self.network = network
        self.client = client or get_docker_client()

        # Containers
        self.mysql_container: Optional[Container] = None
        self.kafka_container: Optional[Container] = None
        self.wiremock_container: Optional[Container] = None
        self.redis_containers: Dict[str, Container] = {}
        self.app_containers: List[Container] = []

        # Endpoints
        self.mysql_host_dsn: str = ""
        self.kafka_broker_addr: str = ""
        self.wiremock_host_url: str = ""
        self.redis_addrs: Dict[str, str] = {}

        # Clients
        self.db: Optional[pymysql.connections.Connection] = None
        self.redis_clients: Dict[str, redis.Redis] = {}

    def redis_client(self, alias: str) -> Optional[redis.Redis]:
        """Returns the active redis client for the given instance alias."""
        return self.redis_clients.get(alias)

    def teardown(self) -> None:
        """Cleanly terminates all containers in reverse order and safely prunes managed containers."""
        # 1. Close client connections
        if self.db:
            try:
                self.db.close()
            except Exception as e:
                logger.debug("Error closing MySQL connection: %s", e)
            self.db = None

        closed_redis_ids = set()
        for alias, rclient in list(self.redis_clients.items()):
            if id(rclient) in closed_redis_ids:
                continue
            try:
                rclient.close()
                closed_redis_ids.add(id(rclient))
            except Exception as e:
                logger.debug("Error closing Redis client [%s]: %s", alias, e)
        self.redis_clients.clear()

        # 2. Terminate application containers
        for app in self.app_containers:
            try:
                app.remove(force=True, v=True)
            except Exception as e:
                logger.warning("Error terminating app container: %s", e)
        self.app_containers.clear()

        # 3. Terminate backing containers
        removed_redis_ids = set()
        for alias, rc in list(self.redis_containers.items()):
            if rc.id in removed_redis_ids:
                continue
            try:
                rc.remove(force=True, v=True)
                removed_redis_ids.add(rc.id)
            except Exception as e:
                logger.warning("Error terminating redis container [%s]: %s", alias, e)
        self.redis_containers.clear()

        if self.mysql_container:
            try:
                self.mysql_container.remove(force=True, v=True)
            except Exception as e:
                logger.warning("Error terminating mysql container: %s", e)
            self.mysql_container = None

        if self.kafka_container:
            try:
                self.kafka_container.remove(force=True, v=True)
            except Exception as e:
                logger.warning("Error terminating kafka container: %s", e)
            self.kafka_container = None

        if self.wiremock_container:
            try:
                self.wiremock_container.remove(force=True, v=True)
            except Exception as e:
                logger.warning("Error terminating wiremock container: %s", e)
            self.wiremock_container = None

        # 4. Remove network
        if self.network:
            try:
                self.network.remove()
            except Exception as e:
                logger.debug("Error removing network [%s]: %s", self.network.name, e)
            self.network = None

        # 5. Safety prune dangling managed containers (never touches images)
        try:
            prune_managed_containers(self.client)
        except Exception as e:
            logger.debug("Error during safety pruning: %s", e)
