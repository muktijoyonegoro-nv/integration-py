"""Consumer-isolated contract test scenario for sort-service."""

import time

import pytest

from harness.contract import (
    new_sort_node_created_event,
    new_sort_node_deleted_event,
    new_sort_node_updated_event,
)
from harness.infra.kafka import publish_proto
from proto.protos_sort.sortmistake import sort_node_pb2
from tests.common.polling import eventually
from tests.sort_service.consume_sort_node.util.db import query_intra_hub_node
from tests.sort_service.consume_sort_node.util.redis import get_sort_service_intra_node

SORT_MISTAKE_NODES_TOPIC = "dev-sort-mistake-evt-nodes"


@pytest.mark.sort_service
@pytest.mark.consumer
def test_sort_service_consumer_event_ingestion(scenario):
    redis_sort = scenario.redis_client("redis-sort")
    assert redis_sort is not None, "redis-sort client must not be None"

    # 1. Per-test state isolation
    scenario.truncate_tables()
    scenario.flush_redis()

    system_id = "sg"
    hub_id = 101
    node_id = 98765
    node_name = "CONSUMER_INJECTED_NODE"
    updated_node_name = "CONSUMER_INJECTED_NODE_UPDATED"

    # =========================================================================
    # STEP 1: INJECT CONTRACT CREATED EVENT & ASSERT CONSUMER SYNC
    # =========================================================================
    created_evt = new_sort_node_created_event(
        system_id=system_id,
        hub_id=hub_id,
        node_id=node_id,
        name=node_name,
        node_type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_MID,
    )
    publish_proto(
        scenario.kafka_broker,
        
        SORT_MISTAKE_NODES_TOPIC,
        
        created_evt,
        
        key=created_evt.system_id,
    )

    def check_created_sync():
        record = query_intra_hub_node(scenario.db, node_id)
        if not record or record.name != node_name:
            return False
        cached_proto = get_sort_service_intra_node(redis_sort, system_id, hub_id, node_id)
        return bool(cached_proto and cached_proto.name == node_name)

    eventually(
        check_created_sync,
        timeout=15.0,
        message="sort-service must consume created event and sync DB + Redis",
    )

    # =========================================================================
    # STEP 2: INJECT CONTRACT UPDATED EVENT & ASSERT CONSUMER SYNC
    # =========================================================================
    updated_evt = new_sort_node_updated_event(
        system_id=system_id,
        hub_id=hub_id,
        node_id=node_id,
        name=updated_node_name,
        node_type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_MID,
    )
    publish_proto(
        scenario.kafka_broker,
        
        SORT_MISTAKE_NODES_TOPIC,
        
        updated_evt,
        
        key=updated_evt.system_id,
    )

    def check_updated_sync():
        record = query_intra_hub_node(scenario.db, node_id)
        if not record or record.name != updated_node_name:
            return False
        cached_proto = get_sort_service_intra_node(redis_sort, system_id, hub_id, node_id)
        return bool(cached_proto and cached_proto.name == updated_node_name)

    eventually(
        check_updated_sync,
        timeout=15.0,
        message="sort-service must consume updated event and update DB + Redis",
    )

    # =========================================================================
    # STEP 3: INJECT CONTRACT DELETED EVENT & ASSERT CONSUMER EVICTION
    # =========================================================================
    deleted_evt = new_sort_node_deleted_event(
        system_id=system_id,
        hub_id=hub_id,
        node_id=node_id,
    )
    publish_proto(
        scenario.kafka_broker,
        
        SORT_MISTAKE_NODES_TOPIC,
        
        deleted_evt,
        
        key=deleted_evt.system_id,
    )

    def check_deleted_sync():
        record = query_intra_hub_node(scenario.db, node_id)
        if record is not None:
            return False
        cached_proto = get_sort_service_intra_node(redis_sort, system_id, hub_id, node_id)
        return cached_proto is None

    eventually(
        check_deleted_sync,
        timeout=15.0,
        message="sort-service must consume deleted event and evict from DB + Redis",
    )

    # =========================================================================
    # STEP 4: CONSUMER IDEMPOTENCY / EDGE CASE VALIDATION
    # =========================================================================
    duplicate_delete_evt = new_sort_node_deleted_event(
        system_id=system_id,
        hub_id=hub_id,
        node_id=node_id,
    )
    publish_proto(
        scenario.kafka_broker,
        
        SORT_MISTAKE_NODES_TOPIC,
        
        duplicate_delete_evt,
        
        key=duplicate_delete_evt.system_id,
    )

    time.sleep(1.0)
    record = query_intra_hub_node(scenario.db, node_id)
    assert record is None, "record must remain deleted after repeated delete event"
