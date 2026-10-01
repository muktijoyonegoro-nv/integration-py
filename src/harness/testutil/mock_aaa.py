"""WireMock authentication mock configuration."""

from __future__ import annotations

import time

import httpx


def setup_wiremock_aaa(wiremock_base_url: str, timeout: float = 30.0) -> None:
    """Configures WireMock to return valid AAA authentication claims for any auth request."""
    stub = {
        "request": {
            "method": "ANY",
            "urlPathPattern": ".*",
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            "jsonBody": {
                "status": "OK",
                "id": 1001,
                "accessToken": "test-valid-token",
                "expirationDate": "2035-01-01T00:00:00Z",
                "data": {
                    "user_id": 1001,
                    "username": "integration_test_operator",
                    "email": "test@ninjavan.co",
                    "client_id": "integration-harness",
                    "scopes": [
                        "SORT_TASKS_ADMIN",
                        "SORT_WAREHOUSE_TASKS_MANAGE",
                        "SORT_WAREHOUSE_TASKS_VIEW",
                        "CORE_GET_WAREHOUSE_SWEEP",
                        "MANAGE_FACILITIES",
                    ],
                },
                "scopes": [
                    "SORT_TASKS_ADMIN",
                    "SORT_WAREHOUSE_TASKS_MANAGE",
                    "SORT_WAREHOUSE_TASKS_VIEW",
                    "CORE_GET_WAREHOUSE_SWEEP",
                    "MANAGE_FACILITIES",
                ],
                "globalScopes": {
                    "sg": [
                        "SORT_TASKS_ADMIN",
                        "SORT_WAREHOUSE_TASKS_MANAGE",
                        "SORT_WAREHOUSE_TASKS_VIEW",
                        "CORE_GET_WAREHOUSE_SWEEP",
                        "MANAGE_FACILITIES",
                    ],
                    "global": [
                        "SORT_TASKS_ADMIN",
                        "SORT_WAREHOUSE_TASKS_MANAGE",
                        "SORT_WAREHOUSE_TASKS_VIEW",
                        "CORE_GET_WAREHOUSE_SWEEP",
                        "MANAGE_FACILITIES",
                    ],
                },
            },
        },
    }

    base = wiremock_base_url.rstrip("/")
    admin_health_url = f"{base}/__admin/health"
    mappings_url = f"{base}/__admin/mappings"

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with httpx.Client(timeout=2.0) as client:
                health_resp = client.get(admin_health_url)
                if health_resp.status_code == 200:
                    resp = client.post(mappings_url, json=stub)
                    resp.raise_for_status()
                    return
        except Exception:
            time.sleep(0.5)

    raise TimeoutError(f"Timed out configuring WireMock at {base} after {timeout}s")
