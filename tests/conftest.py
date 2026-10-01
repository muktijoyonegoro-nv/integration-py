"""Global Pytest configuration and scenario fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

from tests.common.harness import Scenario, setup_scenario


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Generator:
    """Stores the test outcome directly on the test item so fixtures can detect failure."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture
def scenario(request: pytest.FixtureRequest, subtests: pytest.Subtests) -> Generator[Scenario, None, None]:
    """Auto-discovers and sets up the scenario defined in the adjacent config.yaml."""
    test_file = Path(request.path)
    config_path = test_file.parent / "config.yaml"

    if not config_path.is_file():
        raise FileNotFoundError(f"Scenario configuration config.yaml not found adjacent to {test_file}")

    s = setup_scenario(config_path, subtests=subtests)

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
