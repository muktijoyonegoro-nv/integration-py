"""Unit tests for configuration loading, upward directory search, and podman helpers."""

import os
from pathlib import Path

import pytest

from harness.config import (
    DEFAULT_PODMAN_BIN,
    Config,
    find_config_file,
    load_config,
    service_name_to_env_key,
)
from harness.env.podman import get_docker_client, setup_podman_environment
from harness.env.prune import default_labels, prune_managed_containers


def test_service_name_to_env_key():
    assert service_name_to_env_key("sort-mistake") == "SORT_MISTAKE"
    assert service_name_to_env_key("sort_service") == "SORT_SERVICE"
    assert service_name_to_env_key("my-cool-service-v2") == "MY_COOL_SERVICE_V2"


def test_config_defaults(monkeypatch):
    monkeypatch.delenv("SORT_MISTAKE_IMAGE", raising=False)
    monkeypatch.delenv("SORT_MISTAKE_DIR", raising=False)
    monkeypatch.delenv("PODMAN_BIN", raising=False)

    cfg = Config()
    assert cfg.get_podman_bin() == DEFAULT_PODMAN_BIN
    assert cfg.get_image("mysql") == "mysql:8.0"
    assert cfg.get_image("kafka") == "confluentinc/confluent-local:7.6.0"
    assert cfg.get_local_image("sort-mistake") == "sort-mistake:latest"
    assert cfg.get_local_repo_dir("sort-mistake") == "../sort-mistake"


def test_config_env_overrides(monkeypatch):
    monkeypatch.setenv("SORT_MISTAKE_IMAGE", "custom-sort-mistake:v1")
    monkeypatch.setenv("SORT_MISTAKE_DIR", "/custom/dir/sort-mistake")
    monkeypatch.setenv("PODMAN_BIN", "/usr/local/bin/podman-custom")

    cfg = Config()
    assert cfg.get_podman_bin() == "/usr/local/bin/podman-custom"
    assert cfg.get_local_image("sort-mistake") == "custom-sort-mistake:v1"
    assert cfg.get_local_repo_dir("sort-mistake") == "/custom/dir/sort-mistake"


def test_load_config_from_workspace():
    cfg = load_config()
    assert cfg.podman.bin != ""
    assert cfg.get_image("mysql") != ""
    assert cfg.get_image("kafka") != ""


def test_find_config_file_traversal(tmp_path: Path):
    nested_dir = tmp_path / "a" / "b" / "c"
    nested_dir.mkdir(parents=True)
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("podman:\n  bin: /test/bin\n")

    found = find_config_file(nested_dir)
    assert found is not None
    assert found.resolve() == cfg_file.resolve()


def test_default_labels():
    labels = default_labels("sort-mistake")
    assert labels["harness.managed"] == "true"
    assert labels["harness.suite"] == "integration-py"
    assert labels["harness.service"] == "sort-mistake"


def test_podman_socket_and_docker_client():
    client = get_docker_client()
    assert client is not None
    assert client.ping() is True


def test_safe_managed_container_pruning():
    client = get_docker_client()
    # Create a dummy managed container
    labels = default_labels("test-prune-service")
    c = client.containers.run(
        image="redis:7-alpine",
        command=["sleep", "60"],
        detach=True,
        labels=labels,
    )
    cid = c.id
    try:
        # Pruning must clean it up
        prune_managed_containers(client)
        # Verify container no longer exists
        with pytest.raises(Exception):
            client.containers.get(cid)
    finally:
        try:
            c.remove(force=True)
        except Exception:
            pass
