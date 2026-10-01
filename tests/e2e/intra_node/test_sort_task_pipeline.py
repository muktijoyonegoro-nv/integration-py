"""Full E2E multi-service integration test scenario."""

import uuid

import httpx
import pytest

from harness.contract import (
    assert_node_created_contract,
    assert_node_deleted_contract,
    assert_node_updated_contract,
)
from harness.testutil import (
    KafkaProtoReader,
    eventually,
    get_sort_service_intra_node,
    query_intra_hub_node,
)
from proto.protos_sort.sortmistake import sort_node_pb2

SORT_MISTAKE_NODES_TOPIC = "dev-sort-mistake-evt-nodes"


@pytest.mark.e2e
def test_sort_task_pipeline_full_crud_cycle(scenario):
    sort_mistake_base_url = scenario.endpoint("sort-mistake")
    redis_mistake = scenario.redis_client("redis-sort-mistake")
    redis_sort = scenario.redis_client("redis-sort")
    assert redis_mistake is not None, "redis-sort-mistake client must not be None"
    assert redis_sort is not None, "redis-sort client must not be None"

    # 1. Per-test state isolation
    scenario.truncate_tables()
    scenario.flush_redis()

    # 2. Setup Kafka Reader to monitor topic
    reader = KafkaProtoReader(
        broker_addr=scenario.kafka_broker,
        topic=SORT_MISTAKE_NODES_TOPIC,
        group_id=f"pipeline-test-{uuid.uuid4().hex[:8]}",
    )

    try:
        system_id = "sg"
        hub_id = 101
        node_name = "STATION_ALPHA"
        updated_node_name = "STATION_ALPHA_UPDATED"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-valid-token",
            "x-nv-system-id": system_id,
        }

        # =========================================================================
        # STEP 1: CREATE SORT TASK
        # =========================================================================
        create_payload = {
            "name": node_name,
            "type": "NODE_TYPE_INTRA_MID",
        }
        url = f"{sort_mistake_base_url}/1.0/intra/hubs/{hub_id}/nodes"

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=create_payload, headers=headers)
            assert resp.status_code in (200, 201), f"API call failed: {resp.text}"

        received_event = reader.read_next_sort_node_event(timeout=15.0)

        created_node_id = assert_node_created_contract(
            received_event,
            system_id=system_id,
            hub_id=hub_id,
            name=node_name,
            node_type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_MID,
        )

        def check_downstream_sync():
            record = query_intra_hub_node(scenario.db, "sort_service", created_node_id)
            if not record or record.name != node_name:
                return False
            cached_proto = get_sort_service_intra_node(redis_sort, system_id, hub_id, created_node_id)
            if not cached_proto or cached_proto.name != node_name:
                return False
            return True

        eventually(
            check_downstream_sync,
            timeout=15.0,
            message="sort-service must consume create event and populate DB + Redis",
        )

        # Helper to create an intra-hub node and ensure downstream sync
        def create_node_via_api(name: str) -> int:
            with httpx.Client(timeout=15.0) as cl:
                r = cl.post(url, json={"name": name, "type": "NODE_TYPE_INTRA_MID"}, headers=headers)
                assert r.status_code in (200, 201), f"API create failed: {r.text}"

            evt = reader.read_next_sort_node_event(timeout=15.0)
            allocated_id = assert_node_created_contract(
                evt,
                system_id=system_id,
                hub_id=hub_id,
                name=name,
                node_type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_MID,
            )

            def check_sync():
                record = query_intra_hub_node(scenario.db, "sort_service", allocated_id)
                return record is not None and record.name == name

            eventually(check_sync, timeout=15.0, message="sort-service must sync created node")
            return allocated_id

        # =========================================================================
        # STEP 2: UPDATE SORT TASK
        # =========================================================================
        target_node_id = create_node_via_api("STATION_UPDATE_TARGET")
        assert target_node_id > 0

        update_url = f"{sort_mistake_base_url}/1.0/intra/hubs/{hub_id}/nodes/{target_node_id}"
        with httpx.Client(timeout=15.0) as client:
            resp = client.patch(update_url, json={"name": updated_node_name}, headers=headers)
            assert resp.status_code in (200, 204), f"PATCH API call failed: {resp.text}"

        received_update = reader.read_next_sort_node_event(timeout=15.0)
        assert_node_updated_contract(
            received_update,
            system_id=system_id,
            hub_id=hub_id,
            node_id=target_node_id,
            name=updated_node_name,
        )

        def check_update_sync():
            record = query_intra_hub_node(scenario.db, "sort_service", target_node_id)
            if not record or record.name != updated_node_name:
                return False
            cached_proto = get_sort_service_intra_node(redis_sort, system_id, hub_id, target_node_id)
            if not cached_proto or cached_proto.name != updated_node_name:
                return False
            return True

        eventually(
            check_update_sync,
            timeout=15.0,
            message="sort-service must consume update event and update DB + Redis",
        )

        # =========================================================================
        # STEP 3: DELETE SORT TASK
        # =========================================================================
        delete_target_id = create_node_via_api("STATION_DELETE_TARGET")
        assert delete_target_id > 0

        delete_url = f"{sort_mistake_base_url}/1.0/intra/hubs/{hub_id}/nodes/{delete_target_id}"
        with httpx.Client(timeout=15.0) as client:
            resp = client.delete(delete_url, headers=headers)
            assert resp.status_code in (200, 204), f"DELETE API call failed: {resp.text}"

        received_delete = reader.read_next_sort_node_event(timeout=15.0)
        assert_node_deleted_contract(
            received_delete,
            system_id=system_id,
            hub_id=hub_id,
            node_id=delete_target_id,
        )

        def check_delete_sync():
            ss_record = query_intra_hub_node(scenario.db, "sort_service", delete_target_id)
            if ss_record is not None:
                return False
            sm_record = query_intra_hub_node(scenario.db, "sort_mistake", delete_target_id)
            if sm_record is not None:
                return False
            cached_proto = get_sort_service_intra_node(redis_sort, system_id, hub_id, delete_target_id)
            if cached_proto is not None:
                return False
            return True

        eventually(
            check_delete_sync,
            timeout=15.0,
            message="sort-service and sort-mistake must evict deleted node from DB + Redis",
        )

    finally:
        reader.close()
