from common import boolean_pb2 as _boolean_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UpdateString(_message.Message):
    __slots__ = ("oldValue", "newValue")
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    oldValue: str
    newValue: str
    def __init__(self, oldValue: _Optional[str] = ..., newValue: _Optional[str] = ...) -> None: ...

class UpdateDouble(_message.Message):
    __slots__ = ("oldValue", "newValue")
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    oldValue: float
    newValue: float
    def __init__(self, oldValue: _Optional[float] = ..., newValue: _Optional[float] = ...) -> None: ...

class UpdateInteger(_message.Message):
    __slots__ = ("oldValue", "newValue")
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    oldValue: int
    newValue: int
    def __init__(self, oldValue: _Optional[int] = ..., newValue: _Optional[int] = ...) -> None: ...

class UpdateLong(_message.Message):
    __slots__ = ("oldValue", "newValue")
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    oldValue: int
    newValue: int
    def __init__(self, oldValue: _Optional[int] = ..., newValue: _Optional[int] = ...) -> None: ...

class UpdateBoolean(_message.Message):
    __slots__ = ("oldValue", "newValue")
    OLDVALUE_FIELD_NUMBER: _ClassVar[int]
    NEWVALUE_FIELD_NUMBER: _ClassVar[int]
    oldValue: _boolean_pb2.Boolean
    newValue: _boolean_pb2.Boolean
    def __init__(self, oldValue: _Optional[_Union[_boolean_pb2.Boolean, str]] = ..., newValue: _Optional[_Union[_boolean_pb2.Boolean, str]] = ...) -> None: ...
