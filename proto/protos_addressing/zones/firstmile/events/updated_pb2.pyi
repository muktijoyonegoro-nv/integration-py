from common import update_common_pb2 as _update_common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UpdateNullableString(_message.Message):
    __slots__ = ("oldValue", "newValue")
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    oldValue: str
    newValue: str
    def __init__(self, oldValue: _Optional[str] = ..., newValue: _Optional[str] = ...) -> None: ...

class UpdateLongList(_message.Message):
    __slots__ = ("oldValue", "newValue")
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    oldValue: _containers.RepeatedScalarFieldContainer[int]
    newValue: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, oldValue: _Optional[_Iterable[int]] = ..., newValue: _Optional[_Iterable[int]] = ...) -> None: ...

class Updated(_message.Message):
    __slots__ = ("updates",)
    class Field(_message.Message):
        __slots__ = ("hub_id", "name", "short_name", "description", "latitude", "longitude", "polygon", "tag_name", "shipper_ids")
        HUB_ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        SHORT_NAME_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        LATITUDE_FIELD_NUMBER: _ClassVar[int]
        LONGITUDE_FIELD_NUMBER: _ClassVar[int]
        POLYGON_FIELD_NUMBER: _ClassVar[int]
        TAG_NAME_FIELD_NUMBER: _ClassVar[int]
        SHIPPER_IDS_FIELD_NUMBER: _ClassVar[int]
        hub_id: _update_common_pb2.UpdateLong
        name: _update_common_pb2.UpdateString
        short_name: _update_common_pb2.UpdateString
        description: _update_common_pb2.UpdateString
        latitude: _update_common_pb2.UpdateDouble
        longitude: _update_common_pb2.UpdateDouble
        polygon: _update_common_pb2.UpdateString
        tag_name: UpdateNullableString
        shipper_ids: UpdateLongList
        def __init__(self, hub_id: _Optional[_Union[_update_common_pb2.UpdateLong, _Mapping]] = ..., name: _Optional[_Union[_update_common_pb2.UpdateString, _Mapping]] = ..., short_name: _Optional[_Union[_update_common_pb2.UpdateString, _Mapping]] = ..., description: _Optional[_Union[_update_common_pb2.UpdateString, _Mapping]] = ..., latitude: _Optional[_Union[_update_common_pb2.UpdateDouble, _Mapping]] = ..., longitude: _Optional[_Union[_update_common_pb2.UpdateDouble, _Mapping]] = ..., polygon: _Optional[_Union[_update_common_pb2.UpdateString, _Mapping]] = ..., tag_name: _Optional[_Union[UpdateNullableString, _Mapping]] = ..., shipper_ids: _Optional[_Union[UpdateLongList, _Mapping]] = ...) -> None: ...
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    updates: _containers.RepeatedCompositeFieldContainer[Updated.Field]
    def __init__(self, updates: _Optional[_Iterable[_Union[Updated.Field, _Mapping]]] = ...) -> None: ...
