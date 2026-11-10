from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class ZoneType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEFAULT_ZONE_TYPE: _ClassVar[ZoneType]
    STANDARD: _ClassVar[ZoneType]
    RTS: _ClassVar[ZoneType]
DEFAULT_ZONE_TYPE: ZoneType
STANDARD: ZoneType
RTS: ZoneType
