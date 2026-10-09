"""TCP socket polling and readiness waiting utilities."""

from __future__ import annotations

import socket
import time


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 60.0) -> None:
    """Blocks until a TCP port is open and accepting connections on host."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except (OSError, ConnectionRefusedError):
            time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for port {host}:{port} after {timeout}s")
