"""Unit tests for Phases 3 through 6 (Contracts, Testutil, Schema, Services)."""

import pytest

from harness.catalog import ServiceDefinition, SortMistake, SortService
from harness.contract import (
    ExpectedSortNode,
    assert_node_created_contract,
    assert_node_deleted_contract,
    assert_node_updated_contract,
    assert_sort_node_events_contract,
    new_sort_node_created_event,
    new_sort_node_deleted_event,
    new_sort_node_updated_event,
    validate_sort_node_event_schema,
)
from harness.testutil.polling import eventually
from proto.protos_sort.sortmistake import sort_node_pb2
from tests.common.schema import ScenarioConfig, load_scenario_config


def test_contract_created_event_fixtures_and_assertions():
    event = new_sort_node_created_event(
        system_id="SYS_TEST",
        hub_id=101,
        node_id=202,
        name="TEST_NODE",
        node_type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_MID,
    )

    allocated_id = assert_node_created_contract(
        event,
        system_id="SYS_TEST",
        hub_id=101,
        name="TEST_NODE",
        node_type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_MID,
    )
    assert allocated_id == 202


def test_contract_updated_event_fixtures_and_assertions():
    event = new_sort_node_updated_event(
        system_id="SYS_TEST",
        hub_id=101,
        node_id=202,
        name="UPDATED_NODE",
        node_type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_OUTPUT,
    )

    assert_node_updated_contract(
        event,
        system_id="SYS_TEST",
        hub_id=101,
        node_id=202,
        name="UPDATED_NODE",
    )


def test_contract_deleted_event_fixtures_and_assertions():
    event = new_sort_node_deleted_event(
        system_id="SYS_TEST",
        hub_id=101,
        node_id=202,
    )

    assert_node_deleted_contract(
        event,
        system_id="SYS_TEST",
        hub_id=101,
        node_id=202,
    )


def test_contract_validation_failures():
    # Test invalid hub_id on create
    bad_node = sort_node_pb2.SortNode(
        id=1,
        hub_id=0,  # Invalid!
        name="BAD",
        type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_INPUT,
        node_event=sort_node_pb2.NodeEvent.NODE_EVENT_CREATED,
    )
    with pytest.raises(ValueError, match="invalid hub_id"):
        validate_sort_node_event_schema(bad_node)

    # Test empty name on create
    bad_node_name = sort_node_pb2.SortNode(
        id=1,
        hub_id=10,
        name="",  # Invalid!
        type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_INPUT,
        node_event=sort_node_pb2.NodeEvent.NODE_EVENT_CREATED,
    )
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_sort_node_event_schema(bad_node_name)


def test_eventually_helper():
    counter = 0

    def check():
        nonlocal counter
        counter += 1
        return counter >= 3

    assert eventually(check, timeout=1.0, interval=0.05) is True

    # Test failure
    with pytest.raises(AssertionError, match="Condition not met"):
        eventually(lambda: False, timeout=0.1, interval=0.02)


def test_catalog_service_definitions():
    assert SortMistake.name == "sort-mistake"
    assert SortMistake.exposed_ports == ["9000/tcp"]
    assert "DB_HOST" in SortMistake.env

    assert SortService.name == "sort-service"
    assert SortService.exposed_ports == ["9000/tcp"]
    assert "DB_URI" in SortService.env


def test_scenario_config_schema(tmp_path):
    yaml_content = """
name: test/scenario
network_name: test-net
wiremock: true
mysql:
  databases:
    - sort_mistake
  check_tables:
    - sort_mistake.intra_hub_nodes
kafka:
  topics:
    - dev-sort-mistake-evt-nodes
redis_instances:
  - redis-sort-mistake
services:
  - name: sort-mistake
    expose_port: "9000/tcp"
    endpoint_key: sort-mistake
"""
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(yaml_content)

    cfg = load_scenario_config(cfg_file)
    assert cfg.name == "test/scenario"
    assert cfg.wiremock is True
    assert cfg.mysql.databases == ["sort_mistake"]
    assert cfg.kafka.topics == ["dev-sort-mistake-evt-nodes"]
    assert cfg.redis_instances == ["redis-sort-mistake"]
    assert len(cfg.services) == 1
    assert cfg.services[0].name == "sort-mistake"
