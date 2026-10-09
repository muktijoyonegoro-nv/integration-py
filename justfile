# Justfile for integration-py test platform

set dotenv-load := true

# Podman binary discovery
PODMAN_BIN := env_var_or_default("PODMAN_BIN", "/opt/podman/bin/podman")
PODMAN_SOCKET := `{{PODMAN_BIN}} machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}' 2>/dev/null || true`

export DOCKER_HOST := env_var_or_default("DOCKER_HOST", if PODMAN_SOCKET != "" { "unix://" + PODMAN_SOCKET } else { "" })
export TESTCONTAINERS_RYUK_DISABLED := "true"

# Local repository paths & container image tags
SORT_MISTAKE_DIR := env_var_or_default("SORT_MISTAKE_DIR", "../sort-mistake")
SORT_SERVICE_DIR := env_var_or_default("SORT_SERVICE_DIR", "../sort-service")
SORT_MISTAKE_IMAGE := env_var_or_default("SORT_MISTAKE_IMAGE", "sort-mistake:latest")
SORT_SERVICE_IMAGE := env_var_or_default("SORT_SERVICE_IMAGE", "sort-service:latest")

# Default recipe: display help
default:
    @just --list

# Setup environment: sync uv virtualenv and compile Protobufs
setup:
    uv sync --all-extras
    just proto-gen

# Pre-pull public backing infrastructure images defined in config.yaml
pull-images:
    uv run pull-images

# Build sort-mistake local image
build-sort-mistake:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -d "{{SORT_MISTAKE_DIR}}" ]; then
        echo "ERROR: Directory '{{SORT_MISTAKE_DIR}}' not found."
        echo "Please point SORT_MISTAKE_DIR in .env to your local sort-mistake checkout."
        exit 1
    fi
    echo "Building {{SORT_MISTAKE_IMAGE}} from {{SORT_MISTAKE_DIR}}..."
    (cd "{{SORT_MISTAKE_DIR}}" && go mod vendor)
    {{PODMAN_BIN}} build --force-rm -t {{SORT_MISTAKE_IMAGE}} -f docker/sort-mistake.Containerfile {{SORT_MISTAKE_DIR}}
    {{PODMAN_BIN}} image prune -f >/dev/null 2>&1 || true
    echo "{{SORT_MISTAKE_IMAGE}} successfully built."

# Build sort-service local image
build-sort-service:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -d "{{SORT_SERVICE_DIR}}" ]; then
        echo "ERROR: Directory '{{SORT_SERVICE_DIR}}' not found."
        echo "Please point SORT_SERVICE_DIR in .env to your local sort-service checkout."
        exit 1
    fi
    echo "Building {{SORT_SERVICE_IMAGE}} from {{SORT_SERVICE_DIR}}..."
    (cd "{{SORT_SERVICE_DIR}}" && (command -v mise >/dev/null 2>&1 && mise exec -- sbt stage || sbt stage))
    {{PODMAN_BIN}} build --force-rm -t {{SORT_SERVICE_IMAGE}} -f docker/sort-service.Containerfile {{SORT_SERVICE_DIR}}
    {{PODMAN_BIN}} image prune -f >/dev/null 2>&1 || true
    echo "{{SORT_SERVICE_IMAGE}} successfully built."

# Build local application images (overridable: service=all, sort-mistake, or sort-service)
build-image service="all":
    #!/usr/bin/env bash
    if [ "{{service}}" = "all" ]; then
        just build-sort-mistake
        just build-sort-service
        echo "All local application images built successfully."
    elif [ "{{service}}" = "sort-mistake" ]; then
        just build-sort-mistake
    elif [ "{{service}}" = "sort-service" ]; then
        just build-sort-service
    else
        echo "Unknown service: {{service}}"
        exit 1
    fi

# Sync canonical Protobuf definitions from .env paths and compile to Python bindings
proto-gen:
    uv run python scripts/proto_gen.py

# Run integration test suites wrapped with resource consumption monitoring
test target="tests" run="" timeout="15m":
    uv run test-runner uv run pytest -p no:warnings -s {{target}} {{ if run != "" { "-k " + run } else { "" } }}

# Sort-mistake scenario shortcut
test-sort-mistake timeout="5m":
    just test "tests/sort_mistake" "" {{timeout}}

# Sort-service scenario shortcut
test-sort-service timeout="5m":
    just test "tests/sort_service" "" {{timeout}}

# Aliases for producer and consumer suites
test-producer timeout="5m":
    just test "tests/sort_mistake/publish_sort_node" "" {{timeout}}

test-consumer timeout="5m":
    just test "tests/sort_service/consume_sort_node" "" {{timeout}}

# Run tests and output JUnit XML report in reports/junit.xml
test-report target="tests" run="" timeout="15m":
    @mkdir -p reports
    uv run test-runner uv run pytest --junitxml=reports/junit.xml -v {{target}} {{ if run != "" { "-k " + run } else { "" } }}
    @echo "Report generated at reports/junit.xml"

# Safely prune managed test containers (images will NOT be touched)
prune-containers:
    #!/usr/bin/env bash
    echo "Checking for managed test containers (label=harness.managed=true)..."
    CONTAINERS=$({{PODMAN_BIN}} ps -aq --filter "label=harness.managed=true" 2>/dev/null || true)
    if [ -n "$CONTAINERS" ]; then
        echo "Pruning test containers: $CONTAINERS"
        {{PODMAN_BIN}} rm -f $CONTAINERS
        echo "Managed containers successfully pruned."
    else
        echo "No dangling managed test containers found."
    fi

# Safely prune dangling build images
prune-images:
    @echo "Pruning dangling container images..."
    {{PODMAN_BIN}} image prune -f

# Clean up reports, prune test containers, and remove dangling build images
clean: prune-containers prune-images
    rm -rf reports/
