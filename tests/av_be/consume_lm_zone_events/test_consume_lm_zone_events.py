"""Kafka consumer contract for AV last-mile zone Redis cache updates."""

import pytest

from harness.contract.addressing import geobuf_pb2, zone_event_pb2, zone_v4_pb2
from harness.infra.kafka import publish_proto
from tests.common.polling import eventually

LM_TOPIC = "it-av-lm-zones"
SYSTEM_ID = zone_event_pb2.SYSTEM_ID_SG
SYSTEM_KEY = "sg"
ZONE_ID = 900_101
LEGACY_ZONE_ID = 600_101


def _cached_zone(redis_client):
    value = redis_client.hget(f"zonemap:{SYSTEM_KEY}", str(ZONE_ID))
    return zone_v4_pb2.ZoneV4.FromString(value) if value else None


def _event(event, *, name, short_name, tag_name=None, shipper_ids=()):
    zone = zone_event_pb2.ZoneEvent(
        event=event,
        id=ZONE_ID,
        legacy_zone_id=LEGACY_ZONE_ID,
        system_id=SYSTEM_ID,
        name=name,
        type=zone_event_pb2.ZONE_TYPE_STANDARD,
        hub_id=22,
        short_name=short_name,
        description="LM integration zone",
        latitude=1.29027,
        longitude=103.851959,
        polygon=geobuf_pb2.Data(dimensions=2, precision=6),
        shipper_ids=shipper_ids,
    )
    if tag_name is not None:
        zone.tag_name = tag_name
    return zone


@pytest.mark.av_be
@pytest.mark.consumer
def test_av_consumer_updates_last_mile_zone_redis_cache(scenario):
    redis_av = scenario.redis_client("redis-av")
    assert redis_av is not None
    scenario.flush_redis()

    created = _event(
        zone_event_pb2.EVENT_CREATE,
        name="LM Singapore Original",
        short_name="LM-ORIG",
        tag_name="4W",
        shipper_ids=[101, 202],
    )
    publish_proto(scenario.kafka_broker, LM_TOPIC, created, key=SYSTEM_KEY)

    def created_is_cached():
        cached = _cached_zone(redis_av)
        return bool(
            cached
            and cached.name == "LM Singapore Original"
            and cached.legacy_zone_id == LEGACY_ZONE_ID
            and list(cached.shipper_ids) == [101, 202]
            and cached.tag_name == "4W"
        )

    eventually(created_is_cached, timeout=20.0, message="AV must cache the created LM zone")

    updated = _event(
        zone_event_pb2.EVENT_UPDATE,
        name="LM Singapore Updated",
        short_name="LM-UPD",
        tag_name="2W",
        shipper_ids=[],
    )
    publish_proto(scenario.kafka_broker, LM_TOPIC, updated, key=SYSTEM_KEY)

    def update_is_cached():
        cached = _cached_zone(redis_av)
        return bool(
            cached
            and cached.name == "LM Singapore Updated"
            and cached.short_name == "LM-UPD"
            and list(cached.shipper_ids) == []
            and cached.tag_name == "2W"
        )

    eventually(update_is_cached, timeout=20.0, message="AV must replace the cached LM zone on update")

    deleted = _event(zone_event_pb2.EVENT_DELETE, name="", short_name="")
    publish_proto(scenario.kafka_broker, LM_TOPIC, deleted, key=SYSTEM_KEY)
    eventually(
        lambda: _cached_zone(redis_av) is None,
        timeout=20.0,
        message="AV must evict the deleted LM zone from Redis",
    )
