"""Imports generated addressing protobufs without colliding with ``tests.common``."""

import sys
from pathlib import Path

_PROTO_ROOT = Path(__file__).resolve().parents[3] / "proto" / "protos_addressing"
if str(_PROTO_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROTO_ROOT))

from common import metadata_pb2, update_common_pb2
from zone import geobuf_pb2, zone_event_pb2, zone_v4_pb2
from zones.firstmile import first_mile_zone_event_pb2
from zones.firstmile.enums import zone_type_pb2
from zones.firstmile.events import created_pb2, deleted_pb2, updated_pb2

__all__ = [
    "created_pb2",
    "deleted_pb2",
    "first_mile_zone_event_pb2",
    "geobuf_pb2",
    "metadata_pb2",
    "update_common_pb2",
    "updated_pb2",
    "zone_event_pb2",
    "zone_type_pb2",
    "zone_v4_pb2",
]
