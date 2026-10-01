"""Service definition specifications and dynamic container launcher."""

from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

import httpx

from harness.config import load_config
from harness.env.prune import default_labels

if TYPE_CHECKING:
    from docker.models.containers import Container
    from harness.env.environment import TestEnvironment

logger = logging.getLogger(__name__)


@dataclass
class ServiceDefinition:
    """Specification of a testable microservice."""

    name: str
    aliases: List[str]
    default_image: str
    exposed_ports: List[str]
    env: Dict[str, str] = field(default_factory=dict)
    health_path: Optional[str] = "/health"
    readiness_timeout: float = 120.0
    startup_timeout: float = 120.0


class AppContainer:
    """Wrapper around a running service container providing dynamic host-port discovery."""

    def __init__(self, container: Container, definition: ServiceDefinition) -> None:
        self.container = container
        self.definition = definition

    def host_port(self, container_port: str) -> int:
        """Finds the dynamically mapped host port for a container internal port (e.g. '9000/tcp')."""
        self.container.reload()
        ports = self.container.attrs.get("NetworkSettings", {}).get("Ports", {})
        mapping = ports.get(container_port)
        if not mapping:
            raise KeyError(
                f"Container port {container_port} has no host mapping. Available ports: {list(ports.keys())}"
            )
        return int(mapping[0]["HostPort"])

    def host_endpoint(self, container_port: str, scheme: str = "http") -> str:
        """Constructs a full endpoint URL for accessing the container from the host."""
        port = self.host_port(container_port)
        return f"{scheme}://127.0.0.1:{port}"

    def wait_for_readiness(self, primary_port: str) -> None:
        """Polls the container until its primary exposed port (and optional health path) is ready."""
        timeout = self.definition.readiness_timeout or self.definition.startup_timeout
        deadline = time.time() + timeout
        port = self.host_port(primary_port)
        logger.info(f"Waiting for {self.definition.name} readiness on 127.0.0.1:{port}...")

        while time.time() < deadline:
            # 1. Check raw TCP connectivity
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                    pass
            except (OSError, ConnectionRefusedError):
                time.sleep(0.5)
                continue

            # 2. Check HTTP health check if defined
            if self.definition.health_path:
                url = f"http://127.0.0.1:{port}{self.definition.health_path}"
                try:
                    with httpx.Client(timeout=2.0) as client:
                        resp = client.get(url)
                        # Treat any 2xx or 4xx (like 401 Unauthorized if auth is active) as server ready
                        if resp.status_code < 500:
                            logger.info(f"{self.definition.name} ready on port {port} (status {resp.status_code})")
                            return
                except Exception:
                    time.sleep(0.5)
                    continue
            else:
                logger.info(f"{self.definition.name} raw TCP ready on port {port}")
                return

        raise TimeoutError(
            f"Timed out waiting for {self.definition.name} readiness on port {port} after {timeout}s"
        )


def start_service(
    env: TestEnvironment,
    definition: ServiceDefinition,
    image_override: Optional[str] = None,
) -> AppContainer:
    """Launches an application service container with dynamic ephemeral host ports."""
    cfg = load_config()

    if image_override:
        image_name = image_override
    else:
        image_name = cfg.get_local_image(definition.name, definition.default_image)

    # Convert exposed_ports list into docker ports dict for ephemeral binding
    ports_spec = {p: None for p in definition.exposed_ports}

    network_name = env.network.name if env.network else "bridge"
    networking_config = None
    if env.network and definition.aliases:
        networking_config = {
            env.network.name: env.client.api.create_endpoint_config(aliases=definition.aliases)
        }

    labels = default_labels(definition.name)

    container = env.client.containers.run(
        image=image_name,
        detach=True,
        environment=definition.env,
        ports=ports_spec,
        labels=labels,
        network=network_name,
        networking_config=networking_config,
    )

    app = AppContainer(container, definition)
    env.app_containers.append(container)

    # Wait for readiness on the first exposed port
    if definition.exposed_ports:
        primary_port = definition.exposed_ports[0]
        app.wait_for_readiness(primary_port)

    return app
