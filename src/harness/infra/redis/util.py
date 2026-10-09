"""Low-level Redis utilities for caching and Protobuf hash queries."""

from __future__ import annotations

import time

import redis
from google.protobuf.message import Message


def connect_redis(addr: str, timeout: float = 10.0) -> redis.Redis:
    """Connects to Redis at host:port, testing ping until timeout."""
    if ":" in addr:
        host, port_str = addr.split(":", 1)
        port = int(port_str)
    else:
        host = addr
        port = 6379

    client = redis.Redis(host=host, port=port, decode_responses=False)
    deadline = time.time() + timeout
    last_err: Exception | None = None

    while time.time() < deadline:
        try:
            if client.ping():
                return client
        except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
            last_err = e
            time.sleep(0.3)

    raise ConnectionError(f"Failed to connect to Redis at {addr} within {timeout}s: {last_err}")


def flush_redis(client: redis.Redis) -> None:
    """Flushes all keys from the current Redis database."""
    client.flushdb()


def get_proto_hash[T: Message](
    client: redis.Redis,
    key: str,
    field: str,
    proto_cls: type[T],
) -> T | None:
    """Retrieves and deserializes a Protobuf message from a Redis hash field."""
    val = client.hget(key, field)
    if not val:
        return None

    msg = proto_cls()
    msg.ParseFromString(val)
    return msg
