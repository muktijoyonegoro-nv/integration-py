from zones.firstmile.enums import zone_type_pb2 as _zone_type_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Created(_message.Message):
    __slots__ = ("name", "zone_type", "hub_id", "short_name", "description", "latitude", "longitude", "polygon", "tag_name", "shipper_ids")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ZONE_TYPE_FIELD_NUMBER: _ClassVar[int]
    HUB_ID_FIELD_NUMBER: _ClassVar[int]
    SHORT_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    LATITUDE_FIELD_NUMBER: _ClassVar[int]
    LONGITUDE_FIELD_NUMBER: _ClassVar[int]
    POLYGON_FIELD_NUMBER: _ClassVar[int]
    TAG_NAME_FIELD_NUMBER: _ClassVar[int]
    SHIPPER_IDS_FIELD_NUMBER: _ClassVar[int]
    name: str
    zone_type: _zone_type_pb2.ZoneType
    hub_id: int
    short_name: str
    description: str
    latitude: float
    longitude: float
    polygon: str
    tag_name: str
    shipper_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, name: _Optional[str] = ..., zone_type: _Optional[_Union[_zone_type_pb2.ZoneType, str]] = ..., hub_id: _Optional[int] = ..., short_name: _Optional[str] = ..., description: _Optional[str] = ..., latitude: _Optional[float] = ..., longitude: _Optional[float] = ..., polygon: _Optional[str] = ..., tag_name: _Optional[str] = ..., shipper_ids: _Optional[_Iterable[int]] = ...) -> None: ...
