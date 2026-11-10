"""Kafka consumer contract for AV first-mile zone Redis cache updates."""

import pytest

from harness.contract.addressing import (
    created_pb2,
    deleted_pb2,
    first_mile_zone_event_pb2,
    metadata_pb2,
    update_common_pb2,
    updated_pb2,
    zone_type_pb2,
)
from harness.infra.kafka import publish_proto
from tests.common.polling import eventually

FM_TOPIC = "it-av-fm-zones"
SYSTEM_ID = "sg"
ZONE_ID = 800_101
LEGACY_ZONE_ID = 700_101


def _cached_zone(redis_client):
    value = redis_client.hget(f"firstmilezonemap:{SYSTEM_ID}", str(ZONE_ID))
    return first_mile_zone_event_pb2.FirstMileZoneEvent.FromString(value) if value else None


def _event(*, created=None, updated=None, deleted=None):
    return first_mile_zone_event_pb2.FirstMileZoneEvent(
        metadata=metadata_pb2.Metadata(system_id=SYSTEM_ID),
        zone_id=ZONE_ID,
        legacy_zone_id=LEGACY_ZONE_ID,
        created=created,
        updated=updated,
        deleted=deleted,
    )


@pytest.mark.av_be
@pytest.mark.consumer
def test_av_consumer_updates_first_mile_zone_redis_cache(scenario):
    redis_av = scenario.redis_client("redis-av")
    assert redis_av is not None
    scenario.flush_redis()

    created = _event(created=created_pb2.Created(
        name="FM Singapore Original",
        zone_type=zone_type_pb2.STANDARD,
        hub_id=11,
        short_name="FM-ORIG",
        description="original zone",
        latitude=1.3521,
        longitude=103.8198,
        polygon="polygon-v1",
        tag_name="4W",
        shipper_ids=[101, 202],
    ))
    publish_proto(scenario.kafka_broker, FM_TOPIC, created, key=SYSTEM_ID)

    def created_is_cached():
        cached = _cached_zone(redis_av)
        return bool(cached and cached.created.name == "FM Singapore Original")

    eventually(created_is_cached, timeout=20.0, message="AV must cache the created FM zone")

    updated = _event(updated=updated_pb2.Updated(updates=[
        updated_pb2.Updated.Field(name=update_common_pb2.UpdateString(newValue="FM Singapore Updated")),
        updated_pb2.Updated.Field(
            shipper_ids=updated_pb2.UpdateLongList(newValue=[303]),
        ),
        updated_pb2.Updated.Field(
            tag_name=updated_pb2.UpdateNullableString(newValue="2W"),
        ),
    ]))
    publish_proto(scenario.kafka_broker, FM_TOPIC, updated, key=SYSTEM_ID)

    def update_is_cached():
        cached = _cached_zone(redis_av)
        return bool(
            cached
            and cached.created.name == "FM Singapore Updated"
            and list(cached.created.shipper_ids) == [303]
            and cached.created.tag_name == "2W"
            and cached.created.hub_id == 11
        )

    eventually(update_is_cached, timeout=20.0, message="AV must apply the FM update to its cached zone")

    deleted = _event(deleted=deleted_pb2.Deleted())
    publish_proto(scenario.kafka_broker, FM_TOPIC, deleted, key=SYSTEM_ID)
    eventually(
        lambda: _cached_zone(redis_av) is None,
        timeout=20.0,
        message="AV must evict the deleted FM zone from Redis",
    )
