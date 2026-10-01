"""Producer-isolated contract test scenario."""

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
    query_intra_hub_node,
)
from proto.protos_sort.sortmistake import sort_node_pb2

SORT_MISTAKE_NODES_TOPIC = "dev-sort-mistake-evt-nodes"


@pytest.mark.producer
def test_sort_mistake_producer_contract_pipeline(scenario):
    sort_mistake_base_url = scenario.endpoint("sort-mistake")
    redis_mistake = scenario.redis_client("redis-sort-mistake")
    assert redis_mistake is not None, "redis-sort-mistake client must not be None"

    # 1. Per-test state isolation
    scenario.truncate_tables()
    scenario.flush_redis()

    # 2. Setup Kafka Reader to monitor topic
    reader = KafkaProtoReader(
        broker_addr=scenario.kafka_broker,
        topic=SORT_MISTAKE_NODES_TOPIC,
        group_id=f"producer-test-{uuid.uuid4().hex[:8]}",
    )

    try:
        system_id = "sg"
        hub_id = 101
        node_name = "PRODUCER_STATION_ALPHA"
        updated_node_name = "PRODUCER_STATION_ALPHA_UPDATED"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-valid-token",
            "x-nv-system-id": system_id,
        }

        # =========================================================================
        # STEP 1: CREATE NODE VIA API & ASSERT CONTRACT
        # =========================================================================
        create_payload = {
            "name": node_name,
            "type": "NODE_TYPE_INTRA_MID",
        }
        url = f"{sort_mistake_base_url}/1.0/intra/hubs/{hub_id}/nodes"

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=create_payload, headers=headers)
            assert resp.status_code in (200, 201), f"API create failed: {resp.text}"

        received_event = reader.read_next_sort_node_event(timeout=15.0)

        created_node_id = assert_node_created_contract(
            received_event,
            system_id=system_id,
            hub_id=hub_id,
            name=node_name,
            node_type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_MID,
        )
        assert created_node_id > 0, "created node ID must be positive"

        # Assert producer's internal MySQL state
        def check_created_in_db():
            record = query_intra_hub_node(scenario.db, "sort_mistake", created_node_id)
            return record is not None and record.name == node_name

        eventually(check_created_in_db, timeout=10.0, message="sort_mistake must persist created node in DB")

        # =========================================================================
        # HELPER FOR STEPS 2 & 3
        # =========================================================================
        def create_node_via_api(name: str) -> int:
            with httpx.Client(timeout=15.0) as cl:
                r = cl.post(url, json={"name": name, "type": "NODE_TYPE_INTRA_MID"}, headers=headers)
                assert r.status_code in (200, 201), f"API create failed: {r.text}"

            evt = reader.read_next_sort_node_event(timeout=15.0)
            return assert_node_created_contract(
                evt,
                system_id=system_id,
                hub_id=hub_id,
                name=name,
                node_type=sort_node_pb2.NodeType.NODE_TYPE_INTRA_MID,
            )

        # =========================================================================
        # STEP 2: UPDATE NODE VIA API & ASSERT CONTRACT
        # =========================================================================
        target_node_id = create_node_via_api("PRODUCER_UPDATE_TARGET")
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

        def check_updated_in_db():
            record = query_intra_hub_node(scenario.db, "sort_mistake", target_node_id)
            return record is not None and record.name == updated_node_name

        eventually(check_updated_in_db, timeout=10.0, message="sort_mistake must update node in DB")

        # =========================================================================
        # STEP 3: DELETE NODE VIA API & ASSERT CONTRACT
        # =========================================================================
        delete_target_id = create_node_via_api("PRODUCER_DELETE_TARGET")
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

        def check_deleted_in_db():
            record = query_intra_hub_node(scenario.db, "sort_mistake", delete_target_id)
            return record is None

        eventually(check_deleted_in_db, timeout=10.0, message="sort_mistake must delete node from DB")

    finally:
        reader.close()
