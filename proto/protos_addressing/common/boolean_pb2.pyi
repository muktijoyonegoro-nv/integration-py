from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class Boolean(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEFAULT_BOOLEAN_VALUE: _ClassVar[Boolean]
    FALSE: _ClassVar[Boolean]
    TRUE: _ClassVar[Boolean]
DEFAULT_BOOLEAN_VALUE: Boolean
FALSE: Boolean
TRUE: Boolean
