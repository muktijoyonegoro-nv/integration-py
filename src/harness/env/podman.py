"""Environment setup and Podman socket discovery."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional

import docker

from harness.config import DEFAULT_PODMAN_BIN, load_config


def setup_podman_environment() -> Optional[str]:
    """Configures DOCKER_HOST and disables Ryuk for rootless Podman machines.

    Returns the discovered socket path or None.
    """
    os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"

    docker_host = os.getenv("DOCKER_HOST")
    if docker_host:
        return docker_host

    podman_bin = DEFAULT_PODMAN_BIN
    try:
        cfg = load_config()
        podman_bin = cfg.get_podman_bin()
    except Exception:
        pass

    if not shutil.which(podman_bin):
        found = shutil.which("podman")
        if found:
            podman_bin = found

    try:
        res = subprocess.run(
            [podman_bin, "machine", "inspect", "--format", "{{.ConnectionInfo.PodmanSocket.Path}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            socket_path = res.stdout.strip()
            if socket_path:
                host_url = f"unix://{socket_path}"
                os.environ["DOCKER_HOST"] = host_url
                return host_url
    except Exception:
        pass

    return None


def get_docker_client() -> docker.DockerClient:
    """Returns an initialized docker.DockerClient configured with the Podman socket."""
    docker_host = setup_podman_environment()
    if docker_host:
        return docker.DockerClient(base_url=docker_host)
    return docker.from_env()
