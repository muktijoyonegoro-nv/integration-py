"""Scenario connectivity assertion subtests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from harness.testutil.kafka import ensure_topic

if TYPE_CHECKING:
    from tests.common.harness import Scenario


def assert_connectivity(s: Scenario, subtests: pytest.Subtests) -> None:
    """Runs connectivity sanity checks across all configured infrastructure and services."""
    # 1. MySQL Checks
    if s.config.mysql.databases:
        with subtests.test(msg="MySQL Connectivity and Schemas"):
            assert s.db is not None, "MySQL connection pool must not be None"
            with s.db.cursor() as cursor:
                cursor.execute("SELECT 1 AS res;")
                row = cursor.fetchone()
                assert row is not None and row["res"] == 1, "MySQL ping query (SELECT 1) failed"

                for table in s.config.mysql.check_tables:
                    cursor.execute(f"SELECT count(*) AS cnt FROM {table};")
                    cnt_row = cursor.fetchone()
                    assert cnt_row is not None, f"Table check failed for {table}"

    # 2. Redis Checks
    for alias in s.config.redis_instances:
        with subtests.test(msg=f"Redis ({alias}) Connectivity"):
            rclient = s.redis_client(alias)
            assert rclient is not None, f"Redis client for [{alias}] must not be None"
            assert rclient.ping() is True, f"Redis ping failed for [{alias}]"

    # 3. Kafka Checks
    if s.config.kafka.topics or s.kafka_broker:
        with subtests.test(msg="Kafka Broker Connectivity"):
            assert s.kafka_broker != "", "Kafka broker address must not be empty"
            ensure_topic(s.kafka_broker, "harness-connectivity-check", 1, 1, timeout=30.0)

    # 4. WireMock Checks
    if s.config.wiremock:
        with subtests.test(msg="WireMock Auth Mock Connectivity"):
            assert s.wiremock_url != "", "WireMock URL must not be empty"
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{s.wiremock_url.rstrip('/')}/__admin/health")
                assert resp.status_code == 200, f"WireMock health check failed with status {resp.status_code}"

    # 5. Application Services Checks
    for svc in s.config.services:
        key = svc.endpoint_key or svc.name
        if svc.expose_port:
            with subtests.test(msg=f"Service ({key}) Endpoint Check"):
                endpoint = s.endpoint(key)
                assert endpoint != "", f"Endpoint for service [{key}] must not be empty"
