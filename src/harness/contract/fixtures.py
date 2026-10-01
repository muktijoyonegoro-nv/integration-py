"""Synthetic Protobuf contract fixtures."""

from __future__ import annotations

from proto.protos_sort.sortmistake import sort_node_pb2


def new_sort_node_created_event(
    system_id: str,
    hub_id: int,
    node_id: int,
    name: str,
    node_type: sort_node_pb2.NodeType.ValueType,
) -> sort_node_pb2.SortNodeEvents:
    """Creates a contract-compliant SortNodeEvents message for node creation."""
    return sort_node_pb2.SortNodeEvents(
        system_id=system_id,
        type=sort_node_pb2.NodeEventType.NODE_EVENT_TYPE_INTERNAL,
        node=[
            sort_node_pb2.SortNode(
                id=node_id,
                real_id=node_id,
                hub_id=hub_id,
                name=name,
                type=node_type,
                system_id=system_id,
                node_event=sort_node_pb2.NodeEvent.NODE_EVENT_CREATED,
            )
        ],
    )


def new_sort_node_updated_event(
    system_id: str,
    hub_id: int,
    node_id: int,
    name: str,
    node_type: sort_node_pb2.NodeType.ValueType,
) -> sort_node_pb2.SortNodeEvents:
    """Creates a contract-compliant SortNodeEvents message for node update."""
    return sort_node_pb2.SortNodeEvents(
        system_id=system_id,
        type=sort_node_pb2.NodeEventType.NODE_EVENT_TYPE_INTERNAL,
        node=[
            sort_node_pb2.SortNode(
                id=node_id,
                real_id=node_id,
                hub_id=hub_id,
                name=name,
                type=node_type,
                system_id=system_id,
                node_event=sort_node_pb2.NodeEvent.NODE_EVENT_UPDATED,
            )
        ],
    )


def new_sort_node_deleted_event(
    system_id: str,
    hub_id: int,
    node_id: int,
) -> sort_node_pb2.SortNodeEvents:
    """Creates a contract-compliant SortNodeEvents message for node deletion."""
    return sort_node_pb2.SortNodeEvents(
        system_id=system_id,
        type=sort_node_pb2.NodeEventType.NODE_EVENT_TYPE_INTERNAL,
        node=[
            sort_node_pb2.SortNode(
                id=node_id,
                real_id=node_id,
                hub_id=hub_id,
                system_id=system_id,
                node_event=sort_node_pb2.NodeEvent.NODE_EVENT_DELETED,
            )
        ],
    )
