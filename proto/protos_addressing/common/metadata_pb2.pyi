from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Metadata(_message.Message):
    __slots__ = ("system_id", "timestamp", "user_id", "user_grant_type", "user_email", "user_name", "request_id")
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    USER_GRANT_TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_EMAIL_FIELD_NUMBER: _ClassVar[int]
    USER_NAME_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    system_id: str
    timestamp: int
    user_id: int
    user_grant_type: str
    user_email: str
    user_name: str
    request_id: str
    def __init__(self, system_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., user_id: _Optional[int] = ..., user_grant_type: _Optional[str] = ..., user_email: _Optional[str] = ..., user_name: _Optional[str] = ..., request_id: _Optional[str] = ...) -> None: ...
