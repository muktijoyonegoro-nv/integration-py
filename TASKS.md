# Integration Suite: Python Refactoring Task Breakdown

This document provides a granular, phased implementation checklist for refactoring the Go integration testing platform into Python (`integration-py`). Each task includes specific deliverables and verification steps.
Everytime a phase or task is complete, please ensure to mark the checkbox with "x" so that we know the task is completed.

MAKE SURE TO NOT TRUNCATE THE THIS FILE AFTER MARKING THE TASKS AS DONE.

---

## Progress Overview

- [x] **Phase 1: Project Scaffolding & Tooling Setup**
- [x] **Phase 2: Configuration & Podman Runtime Discovery**
- [x] **Phase 3: Backing Infrastructure & Flyway Builder**
- [x] **Phase 4: Service Catalog & Dynamic Container Launcher**
- [x] **Phase 5: Protobuf Compilation, Test Utilities & Contracts**
- [x] **Phase 6: Declarative YAML Schema & Pytest Harness**
- [x] **Phase 7: Test Scenarios Migration**
- [x] **Phase 8: Resource Consumption Monitoring CLI (`test-runner`)**
- [x] **Phase 9: Parity Verification & CI Benchmarking**

---

## Phase 1: Project Scaffolding & Tooling Setup

- [x] **Task 1.1: Initialize `pyproject.toml` with `uv`**
  - Define project metadata (`name = "integration-py"`, Python `>=3.12`).
  - Declare core dependencies: `pydantic`, `pydantic-settings`, `pyyaml`, `python-dotenv`, `docker`, `testcontainers`, `pymysql`, `cryptography`, `redis`, `confluent-kafka`, `protobuf`, `httpx`, `psutil`, `tenacity`.
  - Declare dev dependencies: `pytest`, `pytest-timeout`, `pytest-subtests`, `pytest-xdist`, `grpcio-tools`, `ruff`, `mypy`, typing packages.
  - Configure `hatchling` build backend and tool configs (`pytest`, `ruff`).
  - Configure package directory: `src/harness`.
  - *Verification*: Run `uv sync --all-extras` and ensure `.venv` and `uv.lock` are generated.

- [x] **Task 1.2: Create `.gitignore` and base project skeleton**
  - Add standard Python gitignore rules (`.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`, `reports/`, `*.egg-info/`).
  - Create directory layout: `src/harness/`, `tests/common/`, `proto/`, `docker/`, `scripts/`.
  - *Verification*: Run `git status` to verify clean directory layout.

- [x] **Task 1.3: Copy root assets from `integration-suite`**
  - Copy `config.yaml` with public image versions (`mysql:8.0`, `kafka:7.6.0`, `redis:7-alpine`, `wiremock:3.5.2`, `flyway:11-alpine`).
  - Copy `.env.example` defining `SORT_MISTAKE_DIR`, `SORT_SERVICE_DIR`, `SORT_MISTAKE_IMAGE`, `SORT_SERVICE_IMAGE`.
  - Copy `docker/sort-mistake.Containerfile` and `docker/sort-service.Containerfile`.
  - *Verification*: Confirm files exist and match the Go workspace sources.

- [x] **Task 1.4: Implement `justfile` foundational recipes**
  - Define environment overrides (`PODMAN_BIN`, `PODMAN_SOCKET`, `DOCKER_HOST`, `TESTCONTAINERS_RYUK_DISABLED`).
  - Add recipe `default` (`just --list --unsorted`).
  - Add recipe `setup` (`uv sync --all-extras`).
  - Add recipe `clean` (removes reports, cache directories).
  - Add service build recipes: `build-sort-mistake`, `build-sort-service`, `build-image`.
  - *Verification*: Run `just setup` and `just --list`.

---

## Phase 2: Configuration & Podman Runtime Discovery

- [x] **Task 2.1: Implement root configuration loader (`src/harness/config.py`)**
  - Define `Pydantic` models for `Config`, `PodmanConfig` (binary path and image mappings).
  - Implement upward directory traversal (`find_config_file`, `find_env_file`) from current working directory.
  - Implement `.env` parser preserving existing environment variables.
  - Provide accessor helpers: `get_podman_bin()`, `get_local_image(svc)`, `get_local_repo_dir(svc)`, `get_image(key)`.
  - *Verification*: Write unit test asserting default fallbacks and upward directory resolution.

- [x] **Task 2.2: Implement Podman socket discovery (`src/harness/env/podman.py`)**
  - Inspect rootless Podman machine: `podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}'`.
  - Automatically configure `DOCKER_HOST=unix://<path>` and `TESTCONTAINERS_RYUK_DISABLED=true`.
  - Provide helper `get_docker_client()` initializing `docker.DockerClient` bound to the detected socket.
  - *Verification*: Run script testing `client.ping()` against local Podman machine.

- [x] **Task 2.3: Implement safe container pruning (`src/harness/env/prune.py`)**
  - Filter containers by label `harness.managed=true`.
  - Force-remove matched containers with `remove(force=True, v=True)`.
  - Guarantee zero image deletions (never call `image.remove`).
  - Add `just prune-containers` and `just prune-images` recipes.
  - *Verification*: Spawn dummy container with label `harness.managed=true` and confirm pruning removes it cleanly.

---

## Phase 3: Backing Infrastructure & Flyway Migrations

- [x] **Task 3.1: Implement `TestEnvironment` container manager (`src/harness/env/environment.py`)**
  - Container holder for Network, MySQL, Kafka, Redis instances, WireMock, and AppContainers.
  - Expose client accessors: `db` (`pymysql.Connection`), `redis_client(alias)` (`redis.Redis`), `kafka_broker`, `wiremock_url`.
  - Implement `teardown()` method executing container removals in reverse dependency order, closing connection pools, removing network, and running safety prune.
  - *Verification*: Verify clean teardown with no orphaned containers or network leases left behind.

- [x] **Task 3.2: Implement `EnvironmentBuilder` foundation & network (`src/harness/env/builder.py`)**
  - Fluent builder API: `with_mysql()`, `with_kafka()`, `with_redis_instance()`, `with_wiremock()`.
  - Provision isolated Docker bridge network (e.g. `<scenario>-net`) with container-to-container DNS aliases.
  - Attach standard metadata labels (`harness.managed=true`, `harness.suite=integration-py`, `harness.service=<name>`).
  - *Verification*: Build minimal network and assert presence via Docker client.

- [x] **Task 3.3: Implement MySQL container provisioning & DB initialization**
  - Start container with image `mysql:8.0`, port `3306/tcp`, environment `MYSQL_ROOT_PASSWORD=root`.
  - Wait for listening port readiness probe.
  - Resolve dynamic ephemeral host port.
  - Establish connection pool and execute `CREATE DATABASE IF NOT EXISTS <db>` for all declared databases.
  - *Verification*: Connect from Python host using PyMySQL and assert `SELECT 1` on dynamic port.

- [x] **Task 3.4: Implement Flyway ephemeral migration runner**
  - Auto-discover migration directory from repository checkout (`<service_repo>/resources/db/migration`).
  - Run ephemeral container with `flyway/flyway:11-alpine` attached to scenario network.
  - Mount migrations as read-only volume (`/flyway/sql:ro`).
  - Execute `migrate` command against internal MySQL container (`jdbc:mysql://mysql:3306/<db>`).
  - Wait for container exit; capture logs and raise error if exit code != 0.
  - Terminate and clean up Flyway container upon completion.
  - *Verification*: Run migration against test DB and verify table creation.

- [x] **Task 3.5: Implement Redis instances provisioning**
  - Support multiple named instances (e.g. `redis-sort-mistake`, `redis-sort`).
  - Start containers with `redis:7-alpine`, port `6379/tcp`, attached to scenario network under respective aliases.
  - Resolve ephemeral host ports and initialize `redis.Redis` clients.
  - *Verification*: Send `PING` and assert `PONG` across all instances.

- [x] **Task 3.6: Implement Kafka broker provisioning & topic provisioning**
  - Start Kafka container with `confluentinc/confluent-local:7.6.0`, port `9092/tcp`, network alias `kafka`.
  - Resolve dynamic external host broker endpoint.
  - Pre-provision declared topics using `confluent_kafka.admin.AdminClient`.
  - *Verification*: Verify topics are created and queryable via admin client.

- [x] **Task 3.7: Implement WireMock provisioning & AAA auth mocking**
  - Start WireMock container with `wiremock:3.5.2`, port `8080/tcp`, network alias `mock-services`.
  - Implement `setup_wiremock_aaa(base_url)` registering catch-all OAuth token validation stubs (`POST /__admin/mappings`).
  - *Verification*: Query `GET /__admin/health` and verify HTTP 200 response.

---

## Phase 4: Service Catalog & Dynamic Container Launcher

- [x] **Task 4.1: Define `ServiceDefinition` dataclass (`src/harness/catalog/service.py`)**
  - Define fields: `name`, `default_image`, `aliases`, `exposed_ports`, `env`, `readiness_timeout`.
  - Implement `AppContainer` wrapper storing container handle, service definition, and dynamic port resolver (`host_endpoint(port)`).
  - *Verification*: Typecheck dataclass using mypy.

- [x] **Task 4.2: Implement `SortMistake` catalog spec (`src/harness/catalog/sort_mistake.py`)**
  - Configure default image `sort-mistake:latest`, exposed port `9000/tcp`, alias `sort-mistake`.
  - Configure default env vars (`DB_HOST=mysql:3306`, `NV_KAFKA_SERVERS=kafka:9092`, `NV_REDIS_HOST=redis-sort-mistake:6379`, `NV_AUTH_API_URL=http://mock-services:8080/global/aaa`).
  - *Verification*: Verify env mapping matches Go catalog spec.

- [x] **Task 4.3: Implement `SortService` catalog spec (`src/harness/catalog/sort_service.py`)**
  - Configure default image `sort-service:latest`, exposed port `9000/tcp`, alias `sort-service`.
  - Configure default env vars (`DB_URI=jdbc:mysql://mysql:3306/sort_service`, `NV_KAFKA_SERVERS=kafka:9092`, `NV_REDIS_HOST=redis-sort:6379`, `NV_AUTH_API_URL=http://mock-services:8080/sg/aaa/`).
  - *Verification*: Verify env mapping matches Go catalog spec.

- [x] **Task 4.4: Implement dynamic `start_service` launcher**
  - Resolve image tag: image override -> `.env` override (`<SERVICE>_IMAGE`) -> `default_image`.
  - Attach container to scenario bridge network with internal DNS aliases.
  - Wait for readiness (poll HTTP or TCP port on internal port `9000/tcp` until responding).
  - Map ephemeral host port and store in `scenario.endpoints[service_key]`.
  - *Verification*: Launch mock container service and assert dynamic endpoint resolution.

---

## Phase 5: Protobuf Compilation, Test Utilities & Contracts

- [x] **Task 5.1: Canonical Protobuf Sync & Compilation (`proto/`)**
  - Declare canonical schema file paths in `.env` (e.g. `SORT_NODE_PROTO=${HOME}/.../sort-protos/src/main/protobuf/sortmistake/sort_node.proto`). Fail fast if not configured or file not found.
  - Implement `scripts/proto_gen.py` to auto-discover enclosing SBT project name (`protos-sort`), sanitize to Python package identifier (`protos_sort`), extract relative path under `src/main/protobuf/` (`sortmistake/`), and mirror `.proto` into `proto/protos_sort/sortmistake/`.
  - Ensure `__init__.py` generation across all subpackages.
  - Compile using `grpc_tools.protoc` generating `*_pb2.py` and `*_pb2.pyi`.
  - Add `just proto-gen` recipe invoking `scripts/proto_gen.py`.
  - *Verification*: Run `just proto-gen` and import `SortNode` via `from proto.protos_sort.sortmistake import sort_node_pb2`.

- [x] **Task 5.2: Implement DB utilities (`src/harness/testutil/db.py`)**
  - Implement `connect_mysql(dsn)`.\n  - Implement `truncate_tables(connection, tables)` disabling and re-enabling foreign key checks.
  - Implement `query_intra_hub_node(connection, db_name, node_id)` returning typed dataclass.
  - *Verification*: Test truncation and query against live test container.

- [x] **Task 5.3: Implement Kafka utilities (`src/harness/testutil/kafka.py`)**
  - Implement `ensure_topic(broker, topic)`.
  - Implement `KafkaProtoReader` using `confluent_kafka.Consumer` with unique consumer group UUID, starting from earliest offset.
  - Implement `read_next_sort_node_event(reader, timeout)` unmarshaling protobuf bytes into `SortNodeEvents`.
  - Implement `publish_sort_node_events(broker, topic, events)` producing serialized protobuf bytes.
  - *Verification*: Produce and consume a sample `SortNodeEvents` message.

- [x] **Task 5.4: Implement Redis utilities (`src/harness/testutil/redis.py`)**
  - Implement `connect_redis(addr)`.
  - Implement `flush_redis(client)`.
  - Implement `get_sort_service_intra_node(client, system_id, hub_id, node_id)` unmarshaling binary protobuf stored in Redis hash `intra_node_<sys>_<hub>`.
  - *Verification*: Test hash set/get with protobuf roundtrip.

- [x] **Task 5.5: Implement asynchronous polling helper (`src/harness/testutil/polling.py`)**
  - Implement `eventually(predicate_fn, timeout=15.0, interval=0.2, message="")`.
  - Ensure clear diagnostic output on timeout expiration.
  - *Verification*: Test with instant truth, delayed truth, and expected timeout.

- [x] **Task 5.6: Implement contract fixtures & invariant validators (`src/harness/contract/`)**
  - Port `fixtures.py`: `new_sort_node_created_event`, `new_sort_node_updated_event`, `new_sort_node_deleted_event`.
  - Port `sortmistake.py`: `validate_sort_node_event_schema`, `assert_sort_node_events_contract`, `assert_node_created_contract`, `assert_node_updated_contract`, `assert_node_deleted_contract`.
  - *Verification*: Test contract assertions against valid and intentionally malformed events.

---

## Phase 6: Declarative YAML Schema & Pytest Harness

- [x] **Task 6.1: Implement scenario YAML Pydantic schema (`tests/common/schema.py`)**
  - Define `ScenarioConfig`, `MySQLConfig`, `KafkaConfig`, `ServiceConfig` models.
  - Implement `load_scenario_config(yaml_path)` with strict field validation and default fallbacks.
  - *Verification*: Write unit test asserting invalid YAML throws descriptive validation errors.

- [x] **Task 6.2: Implement automated connectivity checks (`tests/common/connectivity.py`)**
  - Implement `assert_connectivity(env, config)` using `pytest.subtests`:
    - MySQL: `SELECT 1` ping + check table counts.
    - Redis: `PING -> PONG` across all instances.
    - Kafka: create sanity check topic.
    - WireMock: verify `GET /__admin/health` == 200.
    - Application Services: verify mapped endpoints are healthy.
  - *Verification*: Run connectivity check against active test environment.

- [x] **Task 6.3: Implement Pytest scenario fixture (`tests/common/harness.py`)**
  - Implement `scenario` fixture with auto-discovery: `Path(request.path).parent / "config.yaml"`.
  - Build environment using `EnvironmentBuilder` + `ScenarioConfig`.
  - Run connectivity checks before yielding.
  - Handle cleanup on test completion.
  - *Verification*: Create dummy test using fixture and verify setup/teardown sequence.

- [x] **Task 6.4: Implement global Pytest hooks (`tests/conftest.py`)**
  - Register `pytest_runtest_makereport` hook to track test pass/fail status.
  - If test failed, invoke `scenario.dump_logs()` for application services marked with `dump_logs_on_failure: true`.
  - *Verification*: Trigger intentional assertion failure and confirm container logs are dumped to stdout.

---

## Phase 7: Test Scenarios Migration

- [x] **Task 7.1: Migrate Producer-isolated scenario (`tests/producer/intra_node/`)**
  - Create `tests/producer/intra_node/config.yaml` declaring MySQL `sort_mistake`, topic `dev-sort-mistake-evt-nodes`, `redis-sort-mistake`, WireMock, and `sort-mistake` service.
  - Create `tests/producer/intra_node/test_producer_pipeline.py`:
    - Step 1: POST `/1.0/intra/hubs/{hubId}/nodes`, verify Kafka event created contract, assert DB state.
    - Step 2: PATCH `/1.0/intra/hubs/{hubId}/nodes/{nodeId}`, verify update event contract, assert DB state.
    - Step 3: DELETE `/1.0/intra/hubs/{hubId}/nodes/{nodeId}`, verify delete event contract, assert DB eviction.
  - Add recipe `just test-producer`.
  - *Verification*: Execute `just test-producer` against live containers.

- [x] **Task 7.2: Migrate Consumer-isolated scenario (`tests/consumer/intra_node/`)**
  - Create `tests/consumer/intra_node/config.yaml` declaring MySQL `sort_service`, topic `dev-sort-mistake-evt-nodes`, `redis-sort`, WireMock, and `sort-service` container.
  - Create `tests/consumer/intra_node/test_consumer_ingestion.py`:
    - Step 1: Inject synthetic created event -> assert MySQL and Redis sync.
    - Step 2: Inject synthetic updated event -> assert DB and Redis update.
    - Step 3: Inject synthetic deleted event -> assert DB and Redis eviction.
    - Step 4: Validate consumer idempotency on repeated delete event.
  - Add recipe `just test-consumer`.
  - *Verification*: Execute `just test-consumer` against live containers.

- [x] **Task 7.3: Migrate full E2E scenario (`tests/e2e/intra_node/`)**
  - Create `tests/e2e/intra_node/config.yaml` declaring dual DBs, 3 Kafka topics, dual Redis instances, WireMock, and both `sort-mistake` & `sort-service`.
  - Create `tests/e2e/intra_node/test_sort_task_pipeline.py`:
    - Full end-to-end CRUD cycle: API call -> Kafka event -> DB sync -> Redis sync across both microservices.
  - Add recipes `just test-intra-node` and `just test-e2e`.
  - *Verification*: Execute `just test-intra-node` against live containers.

---

## Phase 8: Resource Consumption Monitoring CLI (`test-runner`)

- [x] **Task 8.1: Implement background metrics sampler (`src/harness/runner/monitor.py`)**
  - Monitor host runner: PID, CPU user/sys time, peak RSS via `psutil`.
  - Monitor containers: sample `podman stats --no-stream --format json` every 600ms.
  - Track peak container memory, peak aggregate memory, peak CPU %, concurrent PIDs, Net I/O, Block I/O.
  - Disambiguate container names and resolve image labels (`harness.service`).
  - *Verification*: Run sampler against active containers and verify sampled metrics.

- [x] **Task 8.2: Implement storage delta calculator**
  - Capture initial and final storage via `podman system df --format json`.
  - Capture workspace directory size delta (`.` ignoring `.git`).
  - Capture host disk free delta via `os.statvfs`.
  - *Verification*: Verify accurate delta reporting.

- [x] **Task 8.3: Implement ASCII report generator (`src/harness/runner/reporter.py`)**
  - Format 3-section report matching Go output:
    1. Host Test Runner (Memory RSS, User/Sys CPU time, Avg CPU %).
    2. Containers (Observed list, peak total RAM, per-container breakdown, peak CPU %, PIDs, Net/Block I/O).
    3. Disk & Storage Delta (Podman storage, workspace delta, disk free delta).
  - *Verification*: Compare formatted output string with Go test runner output.

- [x] **Task 8.4: Implement CLI entrypoint & signal traps (`src/harness/runner/cli.py`)**
  - Support `test-runner <cmd> [args...]`.
  - Intercept `SIGINT`, `SIGTERM`, `SIGHUP` and forward to child process.
  - Guarantee ASCII report is printed before exiting, preserving original child exit code.
  - Implement CLI command `pull-images` in `cli.py` to pre-pull public infrastructure images.
  - Register `test-runner` and `pull-images` console scripts in `pyproject.toml`.
  - *Verification*: Run `uv run test-runner pytest tests/producer/intra_node` and verify full report.

---

## Phase 9: Parity Verification & CI Benchmarking

- [x] **Task 9.1: Parity test execution across all suites**
  - Run `just test-producer` -> verify 100% pass, RAM < 1.6 GB, startup < 15s.
  - Run `just test-consumer` -> verify 100% pass, RAM < 2.4 GB.
  - Run `just test-intra-node` -> verify full E2E pipeline passes.
  - *Verification*: Confirm 0 regressions compared to Go implementation.

- [x] **Task 9.2: JUnit XML reporting verification**
  - Run `just test-report`.
  - Verify `reports/junit.xml` conforms to standard schema and reports individual subtests.
  - *Verification*: Inspect `reports/junit.xml` formatting.

- [x] **Task 9.3: Documentation & developer onboarding**
  - Update `README.md` with Python prerequisites (`uv`, `just`, `podman`).
  - Document adding new scenarios:
    1. Create `tests/<repo>/<scenario>/config.yaml`.
    2. Create `tests/<repo>/<scenario>/test_<scenario>.py`.
  - *Verification*: Perform a clean clone test following the README instructions.
