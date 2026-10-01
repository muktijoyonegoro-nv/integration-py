"""Asynchronous polling assertions for state convergence."""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def eventually(
    predicate_fn: Callable[[], T],
    timeout: float = 15.0,
    interval: float = 0.2,
    message: str = "Condition not met within timeout",
) -> T:
    """Repeatedly invokes predicate_fn until it returns a truthy value or timeout expires."""
    deadline = time.time() + timeout
    last_val = None
    last_err: Exception | None = None

    while time.time() < deadline:
        try:
            val = predicate_fn()
            if val:
                return val
            last_val = val
        except Exception as e:
            last_err = e
        time.sleep(interval)

    detail = f"; last returned: {last_val!r}" if last_val is not None else ""
    if last_err:
        detail += f"; last exception: {last_err}"
    raise AssertionError(f"{message} (waited {timeout}s){detail}")
