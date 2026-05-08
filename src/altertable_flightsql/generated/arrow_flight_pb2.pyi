import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CancelStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CANCEL_STATUS_UNSPECIFIED: _ClassVar[CancelStatus]
    CANCEL_STATUS_CANCELLED: _ClassVar[CancelStatus]
    CANCEL_STATUS_CANCELLING: _ClassVar[CancelStatus]
    CANCEL_STATUS_NOT_CANCELLABLE: _ClassVar[CancelStatus]
CANCEL_STATUS_UNSPECIFIED: CancelStatus
CANCEL_STATUS_CANCELLED: CancelStatus
CANCEL_STATUS_CANCELLING: CancelStatus
CANCEL_STATUS_NOT_CANCELLABLE: CancelStatus

class HandshakeRequest(_message.Message):
    __slots__ = ("protocol_version", "payload")
    PROTOCOL_VERSION_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    protocol_version: int
    payload: bytes
    def __init__(self, protocol_version: _Optional[int] = ..., payload: _Optional[bytes] = ...) -> None: ...

class HandshakeResponse(_message.Message):
    __slots__ = ("protocol_version", "payload")
    PROTOCOL_VERSION_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    protocol_version: int
    payload: bytes
    def __init__(self, protocol_version: _Optional[int] = ..., payload: _Optional[bytes] = ...) -> None: ...

class BasicAuth(_message.Message):
    __slots__ = ("username", "password")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    username: str
    password: str
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ActionType(_message.Message):
    __slots__ = ("type", "description")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    type: str
    description: str
    def __init__(self, type: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class Criteria(_message.Message):
    __slots__ = ("expression",)
    EXPRESSION_FIELD_NUMBER: _ClassVar[int]
    expression: bytes
    def __init__(self, expression: _Optional[bytes] = ...) -> None: ...

class Action(_message.Message):
    __slots__ = ("type", "body")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    type: str
    body: bytes
    def __init__(self, type: _Optional[str] = ..., body: _Optional[bytes] = ...) -> None: ...

class Result(_message.Message):
    __slots__ = ("body",)
    BODY_FIELD_NUMBER: _ClassVar[int]
    body: bytes
    def __init__(self, body: _Optional[bytes] = ...) -> None: ...

class SchemaResult(_message.Message):
    __slots__ = ("schema",)
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    schema: bytes
    def __init__(self, schema: _Optional[bytes] = ...) -> None: ...

class FlightDescriptor(_message.Message):
    __slots__ = ("type", "cmd", "path")
    class DescriptorType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[FlightDescriptor.DescriptorType]
        PATH: _ClassVar[FlightDescriptor.DescriptorType]
        CMD: _ClassVar[FlightDescriptor.DescriptorType]
    UNKNOWN: FlightDescriptor.DescriptorType
    PATH: FlightDescriptor.DescriptorType
    CMD: FlightDescriptor.DescriptorType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CMD_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    type: FlightDescriptor.DescriptorType
    cmd: bytes
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, type: _Optional[_Union[FlightDescriptor.DescriptorType, str]] = ..., cmd: _Optional[bytes] = ..., path: _Optional[_Iterable[str]] = ...) -> None: ...

class FlightInfo(_message.Message):
    __slots__ = ("schema", "flight_descriptor", "endpoint", "total_records", "total_bytes", "ordered", "app_metadata")
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    FLIGHT_DESCRIPTOR_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_RECORDS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BYTES_FIELD_NUMBER: _ClassVar[int]
    ORDERED_FIELD_NUMBER: _ClassVar[int]
    APP_METADATA_FIELD_NUMBER: _ClassVar[int]
    schema: bytes
    flight_descriptor: FlightDescriptor
    endpoint: _containers.RepeatedCompositeFieldContainer[FlightEndpoint]
    total_records: int
    total_bytes: int
    ordered: bool
    app_metadata: bytes
    def __init__(self, schema: _Optional[bytes] = ..., flight_descriptor: _Optional[_Union[FlightDescriptor, _Mapping]] = ..., endpoint: _Optional[_Iterable[_Union[FlightEndpoint, _Mapping]]] = ..., total_records: _Optional[int] = ..., total_bytes: _Optional[int] = ..., ordered: bool = ..., app_metadata: _Optional[bytes] = ...) -> None: ...

class PollInfo(_message.Message):
    __slots__ = ("info", "flight_descriptor", "progress", "expiration_time")
    INFO_FIELD_NUMBER: _ClassVar[int]
    FLIGHT_DESCRIPTOR_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    EXPIRATION_TIME_FIELD_NUMBER: _ClassVar[int]
    info: FlightInfo
    flight_descriptor: FlightDescriptor
    progress: float
    expiration_time: _timestamp_pb2.Timestamp
    def __init__(self, info: _Optional[_Union[FlightInfo, _Mapping]] = ..., flight_descriptor: _Optional[_Union[FlightDescriptor, _Mapping]] = ..., progress: _Optional[float] = ..., expiration_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CancelFlightInfoRequest(_message.Message):
    __slots__ = ("info",)
    INFO_FIELD_NUMBER: _ClassVar[int]
    info: FlightInfo
    def __init__(self, info: _Optional[_Union[FlightInfo, _Mapping]] = ...) -> None: ...

class CancelFlightInfoResult(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: CancelStatus
    def __init__(self, status: _Optional[_Union[CancelStatus, str]] = ...) -> None: ...

class Ticket(_message.Message):
    __slots__ = ("ticket",)
    TICKET_FIELD_NUMBER: _ClassVar[int]
    ticket: bytes
    def __init__(self, ticket: _Optional[bytes] = ...) -> None: ...

class Location(_message.Message):
    __slots__ = ("uri",)
    URI_FIELD_NUMBER: _ClassVar[int]
    uri: str
    def __init__(self, uri: _Optional[str] = ...) -> None: ...

class FlightEndpoint(_message.Message):
    __slots__ = ("ticket", "location", "expiration_time", "app_metadata")
    TICKET_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    EXPIRATION_TIME_FIELD_NUMBER: _ClassVar[int]
    APP_METADATA_FIELD_NUMBER: _ClassVar[int]
    ticket: Ticket
    location: _containers.RepeatedCompositeFieldContainer[Location]
    expiration_time: _timestamp_pb2.Timestamp
    app_metadata: bytes
    def __init__(self, ticket: _Optional[_Union[Ticket, _Mapping]] = ..., location: _Optional[_Iterable[_Union[Location, _Mapping]]] = ..., expiration_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., app_metadata: _Optional[bytes] = ...) -> None: ...

class RenewFlightEndpointRequest(_message.Message):
    __slots__ = ("endpoint",)
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    endpoint: FlightEndpoint
    def __init__(self, endpoint: _Optional[_Union[FlightEndpoint, _Mapping]] = ...) -> None: ...

class FlightData(_message.Message):
    __slots__ = ("flight_descriptor", "data_header", "app_metadata", "data_body")
    FLIGHT_DESCRIPTOR_FIELD_NUMBER: _ClassVar[int]
    DATA_HEADER_FIELD_NUMBER: _ClassVar[int]
    APP_METADATA_FIELD_NUMBER: _ClassVar[int]
    DATA_BODY_FIELD_NUMBER: _ClassVar[int]
    flight_descriptor: FlightDescriptor
    data_header: bytes
    app_metadata: bytes
    data_body: bytes
    def __init__(self, flight_descriptor: _Optional[_Union[FlightDescriptor, _Mapping]] = ..., data_header: _Optional[bytes] = ..., app_metadata: _Optional[bytes] = ..., data_body: _Optional[bytes] = ...) -> None: ...

class PutResult(_message.Message):
    __slots__ = ("app_metadata",)
    APP_METADATA_FIELD_NUMBER: _ClassVar[int]
    app_metadata: bytes
    def __init__(self, app_metadata: _Optional[bytes] = ...) -> None: ...

class SessionOptionValue(_message.Message):
    __slots__ = ("string_value", "bool_value", "int64_value", "double_value", "string_list_value")
    class StringListValue(_message.Message):
        __slots__ = ("values",)
        VALUES_FIELD_NUMBER: _ClassVar[int]
        values: _containers.RepeatedScalarFieldContainer[str]
        def __init__(self, values: _Optional[_Iterable[str]] = ...) -> None: ...
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT64_VALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRING_LIST_VALUE_FIELD_NUMBER: _ClassVar[int]
    string_value: str
    bool_value: bool
    int64_value: int
    double_value: float
    string_list_value: SessionOptionValue.StringListValue
    def __init__(self, string_value: _Optional[str] = ..., bool_value: bool = ..., int64_value: _Optional[int] = ..., double_value: _Optional[float] = ..., string_list_value: _Optional[_Union[SessionOptionValue.StringListValue, _Mapping]] = ...) -> None: ...

class SetSessionOptionsRequest(_message.Message):
    __slots__ = ("session_options",)
    class SessionOptionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: SessionOptionValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[SessionOptionValue, _Mapping]] = ...) -> None: ...
    SESSION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    session_options: _containers.MessageMap[str, SessionOptionValue]
    def __init__(self, session_options: _Optional[_Mapping[str, SessionOptionValue]] = ...) -> None: ...

class SetSessionOptionsResult(_message.Message):
    __slots__ = ("errors",)
    class ErrorValue(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[SetSessionOptionsResult.ErrorValue]
        INVALID_NAME: _ClassVar[SetSessionOptionsResult.ErrorValue]
        INVALID_VALUE: _ClassVar[SetSessionOptionsResult.ErrorValue]
        ERROR: _ClassVar[SetSessionOptionsResult.ErrorValue]
    UNSPECIFIED: SetSessionOptionsResult.ErrorValue
    INVALID_NAME: SetSessionOptionsResult.ErrorValue
    INVALID_VALUE: SetSessionOptionsResult.ErrorValue
    ERROR: SetSessionOptionsResult.ErrorValue
    class Error(_message.Message):
        __slots__ = ("value",)
        VALUE_FIELD_NUMBER: _ClassVar[int]
        value: SetSessionOptionsResult.ErrorValue
        def __init__(self, value: _Optional[_Union[SetSessionOptionsResult.ErrorValue, str]] = ...) -> None: ...
    class ErrorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: SetSessionOptionsResult.Error
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[SetSessionOptionsResult.Error, _Mapping]] = ...) -> None: ...
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    errors: _containers.MessageMap[str, SetSessionOptionsResult.Error]
    def __init__(self, errors: _Optional[_Mapping[str, SetSessionOptionsResult.Error]] = ...) -> None: ...

class GetSessionOptionsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetSessionOptionsResult(_message.Message):
    __slots__ = ("session_options",)
    class SessionOptionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: SessionOptionValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[SessionOptionValue, _Mapping]] = ...) -> None: ...
    SESSION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    session_options: _containers.MessageMap[str, SessionOptionValue]
    def __init__(self, session_options: _Optional[_Mapping[str, SessionOptionValue]] = ...) -> None: ...

class CloseSessionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CloseSessionResult(_message.Message):
    __slots__ = ("status",)
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[CloseSessionResult.Status]
        CLOSED: _ClassVar[CloseSessionResult.Status]
        CLOSING: _ClassVar[CloseSessionResult.Status]
        NOT_CLOSEABLE: _ClassVar[CloseSessionResult.Status]
    UNSPECIFIED: CloseSessionResult.Status
    CLOSED: CloseSessionResult.Status
    CLOSING: CloseSessionResult.Status
    NOT_CLOSEABLE: CloseSessionResult.Status
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: CloseSessionResult.Status
    def __init__(self, status: _Optional[_Union[CloseSessionResult.Status, str]] = ...) -> None: ...
