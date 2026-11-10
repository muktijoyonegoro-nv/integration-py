"""Collect per-test eventual-consistency checkpoints for the terminal report."""

from __future__ import annotations

import json
import os
from contextvars import ContextVar, Token
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class CheckpointResult:
    message: str
    status: str


@dataclass
class TestResult:
    name: str
    nodeid: str
    status: str = "FAIL"
    checkpoints: list[CheckpointResult] = field(default_factory=list)


_active_nodeid: ContextVar[str | None] = ContextVar("active_checkpoint_test", default=None)
_results: dict[str, TestResult] = {}


def begin_test(nodeid: str, name: str) -> Token[str | None]:
    """Marks a test as the recipient of checkpoint results."""
    _results[nodeid] = TestResult(name=name, nodeid=nodeid)
    return _active_nodeid.set(nodeid)


def end_test(token: Token[str | None]) -> None:
    """Restores the prior active test context."""
    _active_nodeid.reset(token)


def record_checkpoint(message: str, passed: bool) -> None:
    """Records an eventual-consistency assertion for the currently executing test."""
    nodeid = _active_nodeid.get()
    if nodeid is None or nodeid not in _results:
        return
    _results[nodeid].checkpoints.append(
        CheckpointResult(message=message, status="PASSED" if passed else "FAIL")
    )


def set_test_status(nodeid: str, passed: bool) -> None:
    """Stores the final pytest outcome while retaining any earlier checkpoints."""
    result = _results.get(nodeid)
    if result is not None:
        result.status = "PASSED" if passed else "FAIL"


def write_report() -> None:
    """Writes the collected results when invoked from a test-runner child process."""
    report_path = os.environ.get("HARNESS_CHECKPOINT_REPORT_PATH")
    if not report_path:
        return
    payload = {"tests": [asdict(result) for result in _results.values()]}
    Path(report_path).write_text(json.dumps(payload), encoding="utf-8")
