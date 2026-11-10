from zone import geobuf_pb2 as _geobuf_pb2
from zone import zone_event_pb2 as _zone_event_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ZoneV4(_message.Message):
    __slots__ = ("id", "legacy_zone_id", "system_id", "name", "type", "hub_id", "short_name", "description", "latitude", "longitude", "polygon", "tag_name", "shipper_ids")
    ID_FIELD_NUMBER: _ClassVar[int]
    LEGACY_ZONE_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    HUB_ID_FIELD_NUMBER: _ClassVar[int]
    SHORT_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    LATITUDE_FIELD_NUMBER: _ClassVar[int]
    LONGITUDE_FIELD_NUMBER: _ClassVar[int]
    POLYGON_FIELD_NUMBER: _ClassVar[int]
    TAG_NAME_FIELD_NUMBER: _ClassVar[int]
    SHIPPER_IDS_FIELD_NUMBER: _ClassVar[int]
    id: int
    legacy_zone_id: int
    system_id: _zone_event_pb2.SystemId
    name: str
    type: _zone_event_pb2.ZoneType
    hub_id: int
    short_name: str
    description: str
    latitude: float
    longitude: float
    polygon: _geobuf_pb2.Data
    tag_name: str
    shipper_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, id: _Optional[int] = ..., legacy_zone_id: _Optional[int] = ..., system_id: _Optional[_Union[_zone_event_pb2.SystemId, str]] = ..., name: _Optional[str] = ..., type: _Optional[_Union[_zone_event_pb2.ZoneType, str]] = ..., hub_id: _Optional[int] = ..., short_name: _Optional[str] = ..., description: _Optional[str] = ..., latitude: _Optional[float] = ..., longitude: _Optional[float] = ..., polygon: _Optional[_Union[_geobuf_pb2.Data, _Mapping]] = ..., tag_name: _Optional[str] = ..., shipper_ids: _Optional[_Iterable[int]] = ...) -> None: ...
