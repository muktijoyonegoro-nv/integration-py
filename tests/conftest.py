"""Global Pytest configuration and scenario fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

from harness.env.shared import SharedTestEnvironment
from tests.common.harness import Scenario, setup_scenario


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Generator:
    """Stores the test outcome directly on the test item so fixtures can detect failure."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="session")
def shared_infra(
    request: pytest.FixtureRequest, pytestconfig: pytest.Config
) -> Generator[SharedTestEnvironment, None, None]:
    """Create backing infrastructure once for the selected test scenarios."""
    if hasattr(pytestconfig, "workerinput"):
        raise pytest.UsageError("Shared integration infrastructure does not support pytest-xdist workers")

    config_paths = {
        Path(item.path).parent / "config.yaml"
        for item in request.session.items
        if (Path(item.path).parent / "config.yaml").is_file()
    }
    from tests.common.schema import load_scenario_config

    infra = SharedTestEnvironment.start(load_scenario_config(path) for path in config_paths)
    yield infra
    infra.teardown()


@pytest.fixture
def scenario(
    request: pytest.FixtureRequest,
    subtests: pytest.Subtests,
    shared_infra: SharedTestEnvironment,
) -> Generator[Scenario, None, None]:
    """Auto-discovers and sets up the scenario defined in the adjacent config.yaml."""
    test_file = Path(request.path)
    config_path = test_file.parent / "config.yaml"

    if not config_path.is_file():
        raise FileNotFoundError(f"Scenario configuration config.yaml not found adjacent to {test_file}")

    s = setup_scenario(config_path, subtests=subtests, shared_infra=shared_infra)

    yield s

    # Check if any phase of the test failed
    failed = False
    for when in ("setup", "call", "teardown"):
        rep = getattr(request.node, f"rep_{when}", None)
        if rep and rep.failed:
            failed = True
            break

    if failed:
        s.dump_logs()

    s.teardown()
