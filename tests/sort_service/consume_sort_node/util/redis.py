"""Redis query helpers for sort_service."""

from __future__ import annotations

import redis

from harness.infra.redis import get_proto_hash
from proto.protos_sort.sortmistake import sort_node_pb2


def get_sort_service_intra_node(
    client: redis.Redis,
    system_id: str,
    hub_id: int,
    node_id: int,
) -> sort_node_pb2.SortNode | None:
    """Retrieves and deserializes a SortNode protobuf from Redis hash: intra_node_<sys>_<hub>."""
    key = f"intra_node_{system_id}_{hub_id}"
    field = str(node_id)
    return get_proto_hash(client, key, field, sort_node_pb2.SortNode)
