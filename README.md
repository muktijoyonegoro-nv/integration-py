# Integration Suite (Python)

`integration-py` is a multi-repository integration-test harness for Ninja Van services. It builds local service images, starts real backing services on rootless Podman, and exercises HTTP, MySQL, Redis, Kafka, WireMock, and protobuf contracts through pytest.

The currently supported services are:

- `sort-mistake` — Go producer service.
- `sort-service` — Scala/Play consumer service.

The harness is deliberately integration-oriented: it does not replace MySQL, Kafka, Redis, or service-to-service HTTP with in-process mocks. WireMock is used only for external dependencies such as AAA/Core/Zones.

## Prerequisites

Install and make available on your `PATH`:

- Python 3.12 or later and [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)
- Podman with a running rootless Podman machine/socket
- Go (to build `sort-mistake`)
- Java 11-compatible tooling and SBT (or `mise` configured for SBT) to build `sort-service`
- Local checkouts of `sort-mistake`, `sort-service`, and the repository that owns the canonical sort-node protobuf definition

On macOS, start Podman before running the suite:

```bash
podman machine start
```

The default Podman binary is `/opt/podman/bin/podman`. Override it with `PODMAN_BIN` if needed.

## Initial setup

Create a local environment file, point it at your checkouts, then install dependencies and generate protobuf bindings:

```bash
cp .env.example .env
# Edit .env with absolute paths for your machine.

just setup
```

`.env` is local-only and is loaded automatically. The important settings are:

```dotenv
SORT_MISTAKE_DIR=/absolute/path/to/sort-mistake
SORT_SERVICE_DIR=/absolute/path/to/sort-service

# Optional image tags; these are the defaults used by the tests after building.
SORT_MISTAKE_IMAGE=sort-mistake:local
SORT_SERVICE_IMAGE=sort-service:local

# Exact canonical .proto file, not a copied/generated Python file.
SORT_NODE_PROTO=/absolute/path/to/sort-protos/src/main/protobuf/sortmistake/sort_node.proto
```

You can pre-pull public infrastructure images before the first test run:

```bash
just pull-images
```

The image versions are configured in [`config.yaml`](config.yaml): MySQL 8, Confluent Local Kafka 7.6.0, Redis 7, WireMock 3.5, and Flyway 11.

## Protobuf workflow

Tests consume and assert real Kafka protobuf messages. The canonical schema must come from the source repository rather than being manually copied into this project.

`just proto-gen` runs [`scripts/proto_gen.py`](scripts/proto_gen.py), which:

1. Reads `SORT_NODE_PROTO` from `.env`.
2. Locates the owning SBT project and derives a safe Python package name, such as `protos-sort` → `protos_sort`.
3. Copies the `.proto` source into `proto/<package>/...` while retaining its protobuf-relative path.
4. Runs `grpc_tools.protoc` to create the Python module and type stub beside it.

The tests import the generated types from `proto/`, for example `proto.protos_sort.sortmistake.sort_node_pb2`. Re-run `just proto-gen` whenever the canonical schema changes.

## Build local service images

The test harness starts locally built application images. Build both images before running an affected suite:

```bash
just build-image
```

Or build one service:

```bash
just build-image sort-mistake
just build-image sort-service
```

The build recipes use the directories and tags in `.env`:

- `sort-mistake`: runs `go mod vendor`, then builds the Go service with [`docker/sort-mistake.Containerfile`](docker/sort-mistake.Containerfile).
- `sort-service`: runs `sbt stage` (using `mise` when available), then packages the staged Play application with [`docker/sort-service.Containerfile`](docker/sort-service.Containerfile).

You may override image tags or directories temporarily without editing `.env`:

```bash
SORT_MISTAKE_IMAGE=sort-mistake:my-branch just build-image sort-mistake
SORT_MISTAKE_IMAGE=sort-mistake:my-branch just test-producer
```

## Run tests

Use the `just` recipes for normal runs. They wrap pytest in `test-runner`, which prints resource consumption for only the containers started by that exact command.

```bash
# All selected integration suites
just test

# Service-isolated suites
just test-producer
just test-consumer

# Both services in one workflow
just test-e2e
just test-intra-node

# A specific target or a selected test name
just test tests/producer/intra_node
just test tests producer

# Unit tests do not require application or infrastructure containers
uv run pytest tests/unit

# Write JUnit XML to reports/junit.xml
just test-report tests
```

For direct pytest use, this is also valid:

```bash
uv run pytest tests/producer/intra_node
```

Direct pytest still uses session-shared infrastructure. It simply does not print the `test-runner` resource report.

## How a test run works

Each test directory with a `config.yaml` describes a scenario: needed databases, Kafka topics, Redis DNS aliases, WireMock, and application services. The pytest `scenario` fixture finds the adjacent configuration automatically.

At collection time, the session fixture takes the union of the selected scenario configurations and creates one shared bridge network named `integration-shared-net`. It starts only the requested backing services, then runs Flyway migrations once per database schema.

```text
pytest session
  └─ shared infrastructure starts once
       ├─ MySQL (one server; one or more logical databases)
       ├─ Redis (one server; multiple DNS aliases)
       ├─ Confluent Local Kafka (one broker; declared topics)
       └─ WireMock (AAA default stub)

each test scenario
  ├─ reset shared state
  ├─ start only that scenario's application containers
  ├─ run connectivity subtests and the test body
  └─ remove application containers

pytest session end
  └─ remove shared containers and network
```

The shared model keeps expensive services alive for the session while preserving scenario isolation:

- **MySQL**: one MySQL server hosts `sort_mistake` and/or `sort_service`. Before a scenario, all base tables in configured schemas are truncated with foreign-key checks temporarily disabled.
- **Flyway**: ephemeral Flyway containers apply migrations during session startup only. They do not run again per scenario.
- **Redis**: one Redis container is reachable as both `redis-sort-mistake` and `redis-sort` when both are required. It is flushed before each scenario.
- **Kafka**: one `confluentinc/confluent-local:7.6.0` container hosts all declared topics. Before a scenario, test topics are deleted and recreated so messages and offsets cannot leak to the next scenario. Test consumers also use unique group IDs.
- **WireMock**: one container is reachable as `mock-services`. Its mappings and request journal are reset before each scenario, then the default AAA response stub is restored.
- **Application services**: `sort-mistake` and `sort-service` are intentionally per-scenario. This prevents in-memory state, worker threads, and consumers from one contract test affecting another.

The shared resources make scenarios sequential by design. Do not run these integration suites with `pytest-xdist` (`-n ...`); the harness rejects xdist workers because concurrent state resets would be unsafe.

## Scenario inventory

| Suite | Application containers | MySQL schemas | Kafka topics | Redis alias(es) | WireMock |
| --- | --- | --- | --- | --- | --- |
| `tests/producer/intra_node` | `sort-mistake` | `sort_mistake` | `dev-sort-mistake-evt-nodes` | `redis-sort-mistake` | Yes |
| `tests/consumer/intra_node` | `sort-service` | `sort_service` | `dev-sort-mistake-evt-nodes`, `hub-events-dev-proto-topic`, `dev-hub-evt-shipment-failed-parcel-update` | `redis-sort` | Yes |
| `tests/e2e/intra_node` | `sort-mistake`, `sort-service` | `sort_mistake`, `sort_service` | all three above | `redis-sort-mistake`, `redis-sort` | Yes |

When all suites are selected, the session starts one container each for MySQL, Redis, Kafka, and WireMock, plus an ephemeral Flyway migration container for each migrated schema.

## Container networking and service configuration

Application services receive their infrastructure settings from the service catalog:

- `sort-mistake` connects to `mysql:3306/sort_mistake`, `kafka:9092`, `redis-sort-mistake:6379`, and `http://mock-services:8080`.
- `sort-service` connects to `mysql:3306/sort_service`, `kafka:9092`, `redis-sort:6379`, and `http://mock-services:8080`.

All application ports are published on dynamically chosen host ports. Tests obtain those URLs through `scenario.endpoint("sort-mistake")` or `scenario.endpoint("sort-service")`; do not hard-code host ports in tests.

Scenario-level environment overrides can be placed under `services[].env_overrides` in a scenario `config.yaml`.

## Add a test suite or service

Treat a scenario as a directory containing test modules and one adjacent `config.yaml`. The `scenario` pytest fixture discovers that file from the test module’s directory, so no fixture registration is needed for a new suite.

### Add coverage for an existing service

For another workflow of `sort-mistake` or `sort-service`, create a directory such as `tests/producer/my_workflow/`, add a `config.yaml`, and write tests that request the `scenario` fixture.

```yaml
# tests/producer/my_workflow/config.yaml
name: producer/my_workflow
wiremock: true

mysql:
  databases:
    - sort_mistake
  check_tables:
    - sort_mistake.intra_hub_nodes

kafka:
  topics:
    - dev-sort-mistake-evt-nodes

redis_instances:
  - redis-sort-mistake

services:
  - name: sort-mistake
    endpoint_key: sort-mistake
    expose_port: "9000/tcp"
    env_overrides:
      NV_KAFKA_PRODUCER_ENABLE: "true"
```

Declare every dependency that the test or started application actually uses. The session fixture merges the requirements of all selected scenario files. A test can use the scenario helpers below rather than hard-coding host ports:

```python
def test_example(scenario):
    base_url = scenario.endpoint("sort-mistake")
    redis_client = scenario.redis_client("redis-sort-mistake")
    kafka_bootstrap = scenario.kafka_broker
    wiremock_url = scenario.wiremock_url

    # Explicit cleanup is useful within a multi-step test too.
    scenario.truncate_tables()
    scenario.flush_redis()
```

`check_tables` is a connectivity/schema assertion. It is not the list that controls session cleanup: the shared environment discovers and truncates every base table in each declared MySQL schema.

### Add a new local application repository

Adding a new application means teaching the catalog how to build, start, and reach it, then declaring it in scenarios.

1. Add its local checkout and image tag to `.env`, for example `INVENTORY_SERVICE_DIR` and `INVENTORY_SERVICE_IMAGE`.
2. Add a Containerfile under `docker/` and a `just` build recipe appropriate for that repository’s build output. The existing Go and SBT recipes are examples, not a required build system.
3. Create `src/harness/catalog/inventory_service.py` with a `ServiceDefinition`: its service name, network aliases, default image, exposed ports, health path, and environment. Use bridge-network hostnames such as `mysql`, `kafka`, and `mock-services`, never host-mapped ports.
4. Export it from `src/harness/catalog/__init__.py` and register it in `SERVICE_CATALOG` in `tests/common/harness.py`. A scenario may then list `name: inventory-service` under `services`.
5. Create an adjacent scenario `config.yaml` declaring the databases, topics, Redis aliases, WireMock use, and the new service. Add tests that use `scenario.endpoint("inventory-service")`.
6. Build the image, run that suite directly, then run it with `just test ...` to verify its resource report.

Start with a conservative service definition: map a host port only when a test must make a host-to-container request, and make readiness use a real health endpoint when the application provides one.

### Add MySQL schemas, migrations, topics, or aliases

The current scenario schema supports MySQL, Kafka, Redis, and WireMock. Add a new dependency to the scenario file; the shared session will union it with all other selected suites.

```yaml
mysql:
  databases:
    - inventory_service
  migrations:
    - database: inventory_service
      migration_dir: ../inventory-service/resources/db/migration
  check_tables:
    - inventory_service.stock_items

kafka:
  topics:
    - inventory-events-dev

redis_instances:
  - redis-inventory
```

Use an explicit `migrations` entry for a new service unless its local repository follows the existing convention: a repository named from the database (for example `inventory-service` for `inventory_service`) with migrations at `resources/db/migration`. Explicit paths make the dependency unambiguous.

For Redis, each listed alias resolves to the same shared Redis server. Use a distinct alias when it makes a service’s configuration clearer; it does not create another Redis container in the shared model.

### Add another shared infrastructure type

MySQL, Redis, Kafka, and WireMock are shared infrastructure today. A new shared service—PostgreSQL, OpenSearch, MinIO, a schema registry, and so on—needs more than a container start call: it must have a reproducible reset strategy between scenarios.

Make these coordinated changes:

1. Extend `ScenarioConfig` in `tests/common/schema.py` with a validated configuration section for the new dependency.
2. Extend `EnvironmentBuilder` to start it on `integration-shared-net`, assign required aliases, wait for readiness, and label the container with `default_labels(...)`.
3. Store its container, host endpoint, and client in `TestEnvironment`; close/remove them in `TestEnvironment.teardown()`.
4. Update `SharedTestEnvironment.start()` to merge the dependency configuration across selected scenarios and start exactly one instance.
5. Add a `reset_<dependency>()` method and call it from `prepare_scenario()`. The reset must clear records, queues, buckets, indices, mappings, or stubs that could leak across scenarios.
6. Extend `tests/common/connectivity.py` with an inexpensive health/connectivity subtest, then add focused unit tests for configuration merging and reset behavior.

If reliable reset is impossible or too expensive, keep that component application- or scenario-scoped instead. Shared infrastructure is appropriate only when a clean state can be established without restarting every backing service.

All harness-created containers must use `default_labels(...)`. That supplies `harness.managed=true` for cleanup and, under `test-runner`, the per-run `harness.run_id` used by resource reports. Omitting the helper makes cleanup and resource attribution inaccurate.

## Resource reports

`just test ...` invokes `test-runner`. Each invocation creates a unique `HARNESS_RUN_ID`, which is applied as the `harness.run_id` label to every harness-created container and network. The resource monitor samples Podman but aggregates only containers with that exact label.

This means the report excludes unrelated local workloads, such as another repository's Kafka, Kafka UI, or database containers. The report includes memory, CPU, PIDs, network I/O, block I/O, and storage/workspace deltas for the current run's containers.

## Troubleshooting and cleanup

| Problem | What to check |
| --- | --- |
| Cannot connect to Podman | Run `podman machine start`; set `PODMAN_BIN` or `DOCKER_HOST` if your installation is nonstandard. |
| Image not found | Run `just pull-images` for public images, and `just build-image` for local service images. |
| Protobuf generation fails | Verify `SORT_NODE_PROTO` points to an existing canonical `.proto` and rerun `just proto-gen`. |
| A service cannot reach MySQL/Kafka/Redis | Check its catalog environment and the aliases declared in the scenario `config.yaml`; container-to-container traffic uses DNS aliases, not host ports. |
| A failed run leaves containers behind | Run `just prune-containers`. It only removes containers labeled `harness.managed=true`; it never deletes images. |

To remove dangling build images and reports as well:

```bash
just clean
```

`just clean` does not remove your source repositories, named external volumes, or unrelated Podman workloads.
