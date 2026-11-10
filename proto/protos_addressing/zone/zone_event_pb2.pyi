from zone import geobuf_pb2 as _geobuf_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ZoneType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ZONE_TYPE_UNSPECIFIED: _ClassVar[ZoneType]
    ZONE_TYPE_STANDARD: _ClassVar[ZoneType]
    ZONE_TYPE_RTS: _ClassVar[ZoneType]

class SystemId(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SYSTEM_ID_UNSPECIFIED: _ClassVar[SystemId]
    SYSTEM_ID_SG: _ClassVar[SystemId]
    SYSTEM_ID_MY: _ClassVar[SystemId]
    SYSTEM_ID_ID: _ClassVar[SystemId]
    SYSTEM_ID_TH: _ClassVar[SystemId]
    SYSTEM_ID_PH: _ClassVar[SystemId]
    SYSTEM_ID_VN: _ClassVar[SystemId]
    SYSTEM_ID_MM: _ClassVar[SystemId]
    SYSTEM_ID_MA: _ClassVar[SystemId]

class Event(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EVENT_UNSPECIFIED: _ClassVar[Event]
    EVENT_CREATE: _ClassVar[Event]
    EVENT_UPDATE: _ClassVar[Event]
    EVENT_DELETE: _ClassVar[Event]
    EVENT_REFRESH: _ClassVar[Event]

class Source(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SOURCE_UNSPECIFIED: _ClassVar[Source]
    SOURCE_ADDRESSING: _ClassVar[Source]
    SOURCE_ZONES: _ClassVar[Source]
ZONE_TYPE_UNSPECIFIED: ZoneType
ZONE_TYPE_STANDARD: ZoneType
ZONE_TYPE_RTS: ZoneType
SYSTEM_ID_UNSPECIFIED: SystemId
SYSTEM_ID_SG: SystemId
SYSTEM_ID_MY: SystemId
SYSTEM_ID_ID: SystemId
SYSTEM_ID_TH: SystemId
SYSTEM_ID_PH: SystemId
SYSTEM_ID_VN: SystemId
SYSTEM_ID_MM: SystemId
SYSTEM_ID_MA: SystemId
EVENT_UNSPECIFIED: Event
EVENT_CREATE: Event
EVENT_UPDATE: Event
EVENT_DELETE: Event
EVENT_REFRESH: Event
SOURCE_UNSPECIFIED: Source
SOURCE_ADDRESSING: Source
SOURCE_ZONES: Source

class ZoneEvent(_message.Message):
    __slots__ = ("event", "id", "legacy_zone_id", "system_id", "name", "type", "hub_id", "short_name", "description", "latitude", "longitude", "polygon", "source", "tag_name", "shipper_ids")
    EVENT_FIELD_NUMBER: _ClassVar[int]
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
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TAG_NAME_FIELD_NUMBER: _ClassVar[int]
    SHIPPER_IDS_FIELD_NUMBER: _ClassVar[int]
    event: Event
    id: int
    legacy_zone_id: int
    system_id: SystemId
    name: str
    type: ZoneType
    hub_id: int
    short_name: str
    description: str
    latitude: float
    longitude: float
    polygon: _geobuf_pb2.Data
    source: Source
    tag_name: str
    shipper_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, event: _Optional[_Union[Event, str]] = ..., id: _Optional[int] = ..., legacy_zone_id: _Optional[int] = ..., system_id: _Optional[_Union[SystemId, str]] = ..., name: _Optional[str] = ..., type: _Optional[_Union[ZoneType, str]] = ..., hub_id: _Optional[int] = ..., short_name: _Optional[str] = ..., description: _Optional[str] = ..., latitude: _Optional[float] = ..., longitude: _Optional[float] = ..., polygon: _Optional[_Union[_geobuf_pb2.Data, _Mapping]] = ..., source: _Optional[_Union[Source, str]] = ..., tag_name: _Optional[str] = ..., shipper_ids: _Optional[_Iterable[int]] = ...) -> None: ...
