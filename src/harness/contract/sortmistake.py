"""SortNode contract assertions and invariant validators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from proto.protos_sort.sortmistake import sort_node_pb2


@dataclass
class ExpectedSortNode:
    id: int = 0
    hub_id: int = 0
    system_id: str = ""
    name: str = ""
    type: int = sort_node_pb2.NodeType.NODE_TYPE_UNSPECIFIED
    node_event: int = sort_node_pb2.NodeEvent.NODE_EVENT_UNSPECIFIED


def validate_sort_node_event_schema(
    node: Optional[sort_node_pb2.SortNode],
    expected_event: int = sort_node_pb2.NodeEvent.NODE_EVENT_UNSPECIFIED,
) -> None:
    """Performs strict contract verification on a SortNode message.

    Checks wire formatting, mandatory schema fields, and semantic enum ranges.
    Raises ValueError on contract violation.
    """
    if node is None:
        raise ValueError("Contract violation: SortNode is None")

    if node.id <= 0:
        raise ValueError(f"Contract violation: invalid node.id ({node.id}), must be positive integer")

    if node.node_event == sort_node_pb2.NodeEvent.NODE_EVENT_UNSPECIFIED:
        raise ValueError("Contract violation: node_event is NODE_EVENT_UNSPECIFIED")

    if expected_event != sort_node_pb2.NodeEvent.NODE_EVENT_UNSPECIFIED and node.node_event != expected_event:
        raise ValueError(f"Contract violation: expected node_event {expected_event}, got {node.node_event}")

    # For CREATED and UPDATED events, name, type, and hub_id are mandatory invariants
    if node.node_event in (
        sort_node_pb2.NodeEvent.NODE_EVENT_CREATED,
        sort_node_pb2.NodeEvent.NODE_EVENT_UPDATED,
    ):
        if node.hub_id <= 0:
            raise ValueError(f"Contract violation: invalid hub_id ({node.hub_id}), must be positive integer")
        if not node.name:
            raise ValueError("Contract violation: node name cannot be empty")
        if node.type == sort_node_pb2.NodeType.NODE_TYPE_UNSPECIFIED:
            raise ValueError("Contract violation: node type cannot be NODE_TYPE_UNSPECIFIED")


def assert_sort_node_events_contract(
    events: sort_node_pb2.SortNodeEvents,
    expected: ExpectedSortNode,
) -> None:
    """Validates that a published SortNodeEvents container message satisfies all producer-consumer contract requirements."""
    assert events is not None, "SortNodeEvents must not be None"
    assert events.system_id, "Contract violation: events.system_id must not be empty"

    if expected.system_id:
        assert events.system_id == expected.system_id, f"Contract violation: system_id mismatch ({events.system_id} != {expected.system_id})"

    assert len(events.node) > 0, "Contract violation: events.node list must contain at least one node"
    target_node = events.node[0]

    validate_sort_node_event_schema(target_node, expected.node_event)

    if expected.id > 0:
        assert target_node.id == expected.id, f"Contract violation: node.id mismatch ({target_node.id} != {expected.id})"
    if expected.hub_id > 0:
        assert target_node.hub_id == expected.hub_id, f"Contract violation: node.hub_id mismatch ({target_node.hub_id} != {expected.hub_id})"
    if expected.name:
        assert target_node.name == expected.name, f"Contract violation: node.name mismatch ({target_node.name} != {expected.name})"
    if expected.type != sort_node_pb2.NodeType.NODE_TYPE_UNSPECIFIED:
        assert target_node.type == expected.type, f"Contract violation: node.type mismatch ({target_node.type} != {expected.type})"

    assert target_node.node_event == expected.node_event, f"Contract violation: node.node_event mismatch ({target_node.node_event} != {expected.node_event})"


def assert_node_created_contract(
    events: sort_node_pb2.SortNodeEvents,
    system_id: str,
    hub_id: int,
    name: str,
    node_type: int,
) -> int:
    """Specialized contract assertion for NODE_EVENT_CREATED. Returns the allocated node ID."""
    assert_sort_node_events_contract(
        events,
        ExpectedSortNode(
            hub_id=hub_id,
            system_id=system_id,
            name=name,
            type=node_type,
            node_event=sort_node_pb2.NodeEvent.NODE_EVENT_CREATED,
        ),
    )
    return events.node[0].id


def assert_node_updated_contract(
    events: sort_node_pb2.SortNodeEvents,
    system_id: str,
    hub_id: int,
    node_id: int,
    name: str,
) -> None:
    """Specialized contract assertion for NODE_EVENT_UPDATED."""
    assert_sort_node_events_contract(
        events,
        ExpectedSortNode(
            id=node_id,
            hub_id=hub_id,
            system_id=system_id,
            name=name,
            node_event=sort_node_pb2.NodeEvent.NODE_EVENT_UPDATED,
        ),
    )


def assert_node_deleted_contract(
    events: sort_node_pb2.SortNodeEvents,
    system_id: str,
    hub_id: int,
    node_id: int,
) -> None:
    """Specialized contract assertion for NODE_EVENT_DELETED."""
    assert_sort_node_events_contract(
        events,
        ExpectedSortNode(
            id=node_id,
            hub_id=hub_id,
            system_id=system_id,
            node_event=sort_node_pb2.NodeEvent.NODE_EVENT_DELETED,
        ),
    )
