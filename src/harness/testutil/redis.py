"""Low-level Redis utilities for caching and Protobuf hash queries."""

from __future__ import annotations

import time
from typing import Optional

import redis

from proto.protos_sort.sortmistake import sort_node_pb2


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
    last_err: Optional[Exception] = None

    while time.time() < deadline:
        try:
            if client.ping():
                return client
        except Exception as e:
            last_err = e
            time.sleep(0.3)

    raise ConnectionError(f"Failed to connect to Redis at {addr} within {timeout}s: {last_err}")


def flush_redis(client: redis.Redis) -> None:
    """Flushes all keys from the current Redis database."""
    client.flushdb()


def get_sort_service_intra_node(
    client: redis.Redis,
    system_id: str,
    hub_id: int,
    node_id: int,
) -> Optional[sort_node_pb2.SortNode]:
    """Retrieves and deserializes a SortNode protobuf from Redis hash: intra_node_<sys>_<hub>."""
    key = f"intra_node_{system_id}_{hub_id}"
    field = str(node_id)
    val = client.hget(key, field)
    if not val:
        return None

    node = sort_node_pb2.SortNode()
    node.ParseFromString(val)
    return node
