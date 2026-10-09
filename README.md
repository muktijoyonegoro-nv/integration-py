# integration-py

Multi-repo integration testing platform for Ninja Van logistics microservices using rootless Podman, declarative YAML scenarios, and session-shared backing infrastructure.

The platform provides contract integration tests across:

- `sort-mistake` — Go producer service.
- `sort-service` — Scala/Play consumer service.

Infrastructure services (MySQL 8.0, Apache Kafka 7.6.0, Redis 7, WireMock, and Flyway) are managed as session-scoped singletons through rootless Podman. Only application containers are spun up per scenario.

## Prerequisites

- **macOS** with a running Podman machine, or **Linux** with rootless Podman.
- **Python 3.12+** (Python 3.13 tested).
- **`uv`** (fast Python package and project manager).
- **`just`** (command runner).

Verify that Podman is active:

```bash
podman machine start   # if on macOS
podman info
```

## Quick Start

1. Create a local `.env` from the template:

   ```bash
   cp .env.example .env
   ```

2. Point `.env` to your local service checkouts if you plan to build images locally:

   ```ini
   SORT_MISTAKE_DIR=/path/to/sort-mistake
   SORT_SERVICE_DIR=/path/to/sort-service
   ```

3. Sync the virtualenv and compile Protobufs:

   ```bash
   just setup
   ```

4. Pre-pull the backing infrastructure images:

   ```bash
   just pull-images
   ```

5. Run the integration test suite:

   ```bash
   just test
   ```

## Repository Structure

```text
integration-py/
├── config.yaml               # Centralized backing infrastructure image versions and Podman binary
├── pyproject.toml            # Dependencies and pytest configuration
├── justfile                  # Command runner recipes
├── docker/                   # Containerfiles for local service builds
├── proto/                    # Protobuf schemas and generated Python bindings
│   └── protos_sort/
│       └── sortmistake/
│           ├── sort_node.proto
│           └── sort_node_pb2.py
├── src/harness/              # Core integration harness
│   ├── config.py             # Config discovery and dynamic backing image loader
│   ├── catalog/              # Microservice specifications (SortMistake, SortService)
│   ├── infra/                # Backing infrastructure provisioners & utilities (MySQL, Redis, Kafka, WireMock)
│   ├── env/                  # Runtime environments and EnvironmentBuilder
│   ├── contract/             # Protobuf contract assertion library
│   └── runner/               # Telemetry monitor CLI and ASCII reporters
└── tests/                    # Service-centric integration scenarios
    ├── conftest.py           # Shared session fixtures (shared_infra, scenario)
    ├── common/               # Scenario harness orchestration, connectivity checks, and polling
    ├── sort_mistake/
    │   └── publish_sort_node/
    │       ├── config.yaml
    │       ├── test_publish_sort_node.py
    │       └── util/
    └── sort_service/
        └── consume_sort_node/
            ├── config.yaml
            ├── test_consume_sort_node.py
            └── util/
```

## Build local application images

If you want to test code changes from your local checkouts rather than existing images:

```bash
# Build all local images
just build-image

# Build only one service
just build-sort-mistake
just build-sort-service
```

Each recipe uses the local repository's native tooling:

- `sort-mistake`: runs `go mod vendor`, then builds with [`docker/sort-mistake.Containerfile`](docker/sort-mistake.Containerfile).
- `sort-service`: runs `sbt stage` (using `mise` when available), then packages the staged Play application with [`docker/sort-service.Containerfile`](docker/sort-service.Containerfile).

You may override image tags or directories temporarily without editing `.env`:

```bash
SORT_MISTAKE_IMAGE=sort-mistake:my-branch just build-image sort-mistake
SORT_MISTAKE_IMAGE=sort-mistake:my-branch just test-sort-mistake
```

## Run tests

Use the `just` recipes for normal runs. They wrap pytest in `test-runner`, which prints resource consumption for only the containers started by that exact command.

```bash
# All selected integration suites
just test

# Service-isolated suites
just test-sort-mistake
just test-sort-service

# Suite aliases for producer and consumer
just test-producer
just test-consumer

# A specific target or a selected test name
just test tests/sort_mistake/publish_sort_node
just test tests sort_mistake

# Write JUnit XML to reports/junit.xml
just test-report tests
```

For direct pytest use, this is also valid:

```bash
uv run pytest tests/sort_mistake/publish_sort_node
```

Direct pytest still uses session-shared infrastructure. It simply does not print the `test-runner` resource report.

## How a test run works

Each test directory with a `config.yaml` describes a scenario: needed databases, Kafka topics, Redis DNS aliases, WireMock, and application services. The pytest `scenario` fixture finds the adjacent configuration automatically.

At collection time, the session fixture takes the union of the selected scenario configurations and creates one shared bridge network named `integration-shared-net`. It starts only the requested backing services, then runs Flyway migrations once per database schema.

```text
pytest session start
  ├─ inspect all selected tests/**/config.yaml
  ├─ start integration-shared-net
  ├─ start singleton MySQL, Redis, Kafka, WireMock
  └─ run Flyway migrations once for each database

scenario 1 (e.g. tests/sort_mistake/publish_sort_node)
  ├─ reset: truncate tables, flush redis, delete & recreate kafka topics, reset wiremock
  ├─ start sort-mistake container on integration-shared-net
  ├─ wait for health checks
  ├─ run test cases
  └─ stop and remove sort-mistake container

scenario 2 (e.g. tests/sort_service/consume_sort_node)
  ├─ reset: truncate tables, flush redis, delete & recreate kafka topics, reset wiremock
  ├─ start sort-service container on integration-shared-net
  ├─ wait for health checks
  ├─ run test cases
  └─ stop and remove sort-service container

pytest session finish
  └─ stop and remove all backing infrastructure containers and network
```

- **MySQL**: all databases are created in one MySQL 8.0 instance. Between scenarios, base tables in each database are truncated while preserving schema definitions.
- **Redis**: physical Redis 7 instances are reused. Between scenarios, each instance is flushed (`FLUSHALL`).
- **Kafka**: one `confluentinc/confluent-local:7.6.0` container hosts all declared topics. Before a scenario, test topics are deleted and recreated so messages and offsets cannot leak to the next scenario. Test consumers also use unique group IDs.
- **WireMock**: one WireMock 3.5 container handles authentication and HTTP stubs. Between scenarios, WireMock mappings and request logs are reset.
- **Application services**: `sort-mistake` and `sort-service` are intentionally per-scenario. This prevents in-memory state, worker threads, and consumers from one contract test affecting another.

The shared resources make scenarios sequential by design. Do not run these integration suites with `pytest-xdist` (`-n ...`); the harness rejects xdist workers because concurrent state resets would be unsafe.

## Scenario inventory

| Suite | Application containers | MySQL schemas | Kafka topics | Redis alias(es) | WireMock |
| --- | --- | --- | --- | --- | --- |
| `tests/sort_mistake/publish_sort_node` | `sort-mistake` | `sort_mistake` | `dev-sort-mistake-evt-nodes` | `redis-sort-mistake` | Yes |
| `tests/sort_service/consume_sort_node` | `sort-service` | `sort_service` | `dev-sort-mistake-evt-nodes`, `hub-events-dev-proto-topic`, `dev-hub-evt-shipment-failed-parcel-update` | `redis-sort` | Yes |

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

For another workflow of `sort-mistake` or `sort-service`, create a directory such as `tests/sort_mistake/my_workflow/`, add a `config.yaml`, and write tests that request the `scenario` fixture.

```yaml
# tests/sort_mistake/my_workflow/config.yaml
name: sort_mistake/my_workflow
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
```

In the test file:
```python
def test_example(scenario):
    base_url = scenario.endpoint("sort-mistake")
    redis_client = scenario.redis_client("redis-sort-mistake")
    kafka_bootstrap = scenario.kafka_broker
    wiremock_url = scenario.wiremock_url

    # Automatic cleanup defaults to scenario's mysql.check_tables
    scenario.truncate_tables()
    scenario.flush_redis()
```

### Add a new local application repository

Adding a new application means teaching the catalog how to build, start, and reach it, then declaring it in scenarios.

1. Add its local checkout and image tag to `.env`, for example `INVENTORY_SERVICE_DIR` and `INVENTORY_SERVICE_IMAGE`.
2. Add a Containerfile under `docker/` and a `just` build recipe appropriate for that repository’s build output. The existing Go and SBT recipes are examples, not a required build system.
3. Create `src/harness/catalog/inventory_service.py` with a `ServiceDefinition`: its service name, network aliases, default image, exposed ports, health path, and environment. Use bridge-network hostnames such as `mysql`, `kafka`, and `mock-services`, never host-mapped ports.
4. Export it from `src/harness/catalog/__init__.py` and register it in `SERVICE_CATALOG` in `tests/common/harness.py`. A scenario may then list `name: inventory-service` under `services`.
5. Create an adjacent scenario `config.yaml` declaring the databases, topics, Redis aliases, WireMock use, and the new service. Add tests that use `scenario.endpoint("inventory-service")`.
6. Build the image, run that suite directly, then run it with `just test ...` to verify its resource report.

## Telemetry and Resource Monitoring

The platform includes a built-in telemetry CLI (`test-runner`) that monitors host resources and container stats via the Podman socket during test runs:

- **Host RSS / Peak Memory**: uses `getrusage(RUSAGE_CHILDREN)`.
- **Container Resource Metrics**: samples CPU %, memory usage, PIDs, network I/O, and block I/O every 600ms via `podman stats --no-stream --format json`.
- **Storage Deltas**: captures container layer storage deltas via `podman system df --format json` before and after test execution.

To run tests with resource reporting:

```bash
just test
```

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
