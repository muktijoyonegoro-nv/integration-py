"""Configuration discovery, Pydantic schema validation, and environment loading."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

DEFAULT_PODMAN_BIN = "/opt/podman/bin/podman"

DEFAULT_BACKING_IMAGES = {
    "mysql": "mysql:8.0",
    "redis": "redis:7-alpine",
    "kafka": "confluentinc/confluent-local:7.6.0",
    "wiremock": "docker.io/wiremock/wiremock:3.5.2",
    "flyway": "docker.io/flyway/flyway:11-alpine",
}


def service_name_to_env_key(name: str) -> str:
    """Converts a kebab-case or snake_case service name to an uppercase ENV key."""
    return name.replace("-", "_").upper()


class PodmanConfig(BaseModel):
    bin: str = Field(default=DEFAULT_PODMAN_BIN)
    images: Dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_BACKING_IMAGES))


class Config(BaseModel):
    podman: PodmanConfig = Field(default_factory=PodmanConfig)

    def get_podman_bin(self) -> str:
        """Returns the configured Podman binary path, checking PODMAN_BIN env, config, or default."""
        env_bin = os.getenv("PODMAN_BIN")
        if env_bin:
            return env_bin
        if self.podman.bin:
            return self.podman.bin
        return DEFAULT_PODMAN_BIN

    def get_local_image(self, service_name: str, default_value: str = "") -> str:
        """Resolves an image tag for a local application service.

        Checks <SERVICE>_IMAGE env var, falling back to default_value, or <service_name>:latest.
        """
        env_var = f"{service_name_to_env_key(service_name)}_IMAGE"
        val = os.getenv(env_var)
        if val:
            return val
        if default_value:
            return default_value
        return f"{service_name}:latest"

    def get_local_repo_dir(self, service_name: str, default_dir: str = "") -> str:
        """Resolves the local repository filesystem directory for a service.

        Checks <SERVICE>_DIR env var, falling back to default_dir, or ../<service_name>.
        """
        env_var = f"{service_name_to_env_key(service_name)}_DIR"
        val = os.getenv(env_var)
        if val:
            return val
        if default_dir:
            return default_dir
        return f"../{service_name}"

    def get_image(self, key: str, fallback: str = "") -> str:
        """Resolves an infrastructure image by key (e.g. 'mysql', 'redis', 'kafka').

        Precedence:
        1. podman.images in config.yaml (for public backing infrastructure)
        2. fallback parameter
        3. Built-in defaults in DEFAULT_BACKING_IMAGES
        """
        if self.podman.images and key in self.podman.images and self.podman.images[key]:
            return self.podman.images[key]
        if fallback:
            return fallback
        return DEFAULT_BACKING_IMAGES.get(key, "")


def find_config_file(start_dir: Optional[Path | str] = None) -> Path:
    """Searches for config.yaml starting from start_dir (or current working directory) and walking upwards."""
    env_path = os.getenv("CONFIG_PATH")
    if env_path:
        return Path(env_path)

    curr = Path(start_dir).resolve() if start_dir else Path.cwd().resolve()
    while True:
        candidate = curr / "config.yaml"
        if candidate.is_file():
            return candidate
        if curr.parent == curr:
            break
        curr = curr.parent

    return Path.cwd() / "config.yaml"


def find_env_file(start_dir: Optional[Path | str] = None) -> Optional[Path]:
    """Searches for .env starting from start_dir (or current working directory) and walking upwards."""
    curr = Path(start_dir).resolve() if start_dir else Path.cwd().resolve()
    while True:
        candidate = curr / ".env"
        if candidate.is_file():
            return candidate
        if curr.parent == curr:
            break
        curr = curr.parent

    return None


def load_env() -> None:
    """Discovers and loads .env variables into os.environ if present."""
    env_file = find_env_file()
    if env_file and env_file.is_file():
        load_dotenv(env_file, override=False)


def load_config() -> Config:
    """Loads and parses config.yaml into the Config model, also loading .env."""
    load_env()
    config_path = find_config_file()
    if not config_path.is_file():
        return Config()

    content = config_path.read_text(encoding="utf-8")
    data = yaml.safe_load(content) or {}
    return Config.model_validate(data)
