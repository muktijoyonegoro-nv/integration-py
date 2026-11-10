from common import metadata_pb2 as _metadata_pb2
from zones.firstmile.events import created_pb2 as _created_pb2
from zones.firstmile.events import updated_pb2 as _updated_pb2
from zones.firstmile.events import deleted_pb2 as _deleted_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class FirstMileZoneEvent(_message.Message):
    __slots__ = ("metadata", "zone_id", "legacy_zone_id", "created", "updated", "deleted")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ZONE_ID_FIELD_NUMBER: _ClassVar[int]
    LEGACY_ZONE_ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    UPDATED_FIELD_NUMBER: _ClassVar[int]
    DELETED_FIELD_NUMBER: _ClassVar[int]
    metadata: _metadata_pb2.Metadata
    zone_id: int
    legacy_zone_id: int
    created: _created_pb2.Created
    updated: _updated_pb2.Updated
    deleted: _deleted_pb2.Deleted
    def __init__(self, metadata: _Optional[_Union[_metadata_pb2.Metadata, _Mapping]] = ..., zone_id: _Optional[int] = ..., legacy_zone_id: _Optional[int] = ..., created: _Optional[_Union[_created_pb2.Created, _Mapping]] = ..., updated: _Optional[_Union[_updated_pb2.Updated, _Mapping]] = ..., deleted: _Optional[_Union[_deleted_pb2.Deleted, _Mapping]] = ...) -> None: ...
