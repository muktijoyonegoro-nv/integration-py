from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NodeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NODE_TYPE_UNSPECIFIED: _ClassVar[NodeType]
    NODE_TYPE_HUB: _ClassVar[NodeType]
    NODE_TYPE_MIDDLE: _ClassVar[NodeType]
    NODE_TYPE_ZONE: _ClassVar[NodeType]
    NODE_TYPE_INTRA_INPUT: _ClassVar[NodeType]
    NODE_TYPE_INTRA_MID: _ClassVar[NodeType]
    NODE_TYPE_INTRA_OUTPUT: _ClassVar[NodeType]

class NodeEvent(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NODE_EVENT_UNSPECIFIED: _ClassVar[NodeEvent]
    NODE_EVENT_CREATED: _ClassVar[NodeEvent]
    NODE_EVENT_UPDATED: _ClassVar[NodeEvent]
    NODE_EVENT_DELETED: _ClassVar[NodeEvent]

class NodeEventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NODE_EVENT_TYPE_UNSPECIFIED: _ClassVar[NodeEventType]
    NODE_EVENT_TYPE_INTERNAL: _ClassVar[NodeEventType]
    NODE_EVENT_TYPE_EXTERNAL: _ClassVar[NodeEventType]

class NodeError(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NODE_ERROR_UNSPECIFIED: _ClassVar[NodeError]
    NODE_ERROR_DATABASE: _ClassVar[NodeError]
    NODE_ERROR_REDIS: _ClassVar[NodeError]
    NODE_ERROR_KAFKA: _ClassVar[NodeError]

class PathEvent(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PATH_EVENT_UNSPECIFIED: _ClassVar[PathEvent]
    PATH_EVENT_CREATED: _ClassVar[PathEvent]
    PATH_EVENT_UPDATED: _ClassVar[PathEvent]
    PATH_EVENT_DELETED: _ClassVar[PathEvent]

class ZoneFilterEvent(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ZONE_FILTER_EVENT_UNSPECIFIED: _ClassVar[ZoneFilterEvent]
    ZONE_FILTER_EVENT_CREATED: _ClassVar[ZoneFilterEvent]
    ZONE_FILTER_EVENT_UPDATED: _ClassVar[ZoneFilterEvent]
    ZONE_FILTER_EVENT_DELETED: _ClassVar[ZoneFilterEvent]

class OrderTagFilterEvent(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ORDER_TAG_FILTER_EVENT_UNSPECIFIED: _ClassVar[OrderTagFilterEvent]
    ORDER_TAG_FILTER_EVENT_CREATED: _ClassVar[OrderTagFilterEvent]
    ORDER_TAG_FILTER_EVENT_UPDATED: _ClassVar[OrderTagFilterEvent]
    ORDER_TAG_FILTER_EVENT_DELETED: _ClassVar[OrderTagFilterEvent]

class OutputNodeEvent(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OUTPUT_NODE_EVENT_UNSPECIFIED: _ClassVar[OutputNodeEvent]
    OUTPUT_NODE_EVENT_CREATED: _ClassVar[OutputNodeEvent]
    OUTPUT_NODE_EVENT_UPDATED: _ClassVar[OutputNodeEvent]
    OUTPUT_NODE_EVENT_DELETED: _ClassVar[OutputNodeEvent]

class MapEvent(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MAP_EVENT_UNSPECIFIED: _ClassVar[MapEvent]
    MAP_EVENT_CREATED: _ClassVar[MapEvent]
    MAP_EVENT_UPDATED: _ClassVar[MapEvent]
    MAP_EVENT_DELETED: _ClassVar[MapEvent]

class MapError(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MAP_ERROR_UNSPECIFIED: _ClassVar[MapError]
    MAP_ERROR_GENERATE: _ClassVar[MapError]
    MAP_ERROR_STORE: _ClassVar[MapError]
    MAP_ERROR_PUBLISH: _ClassVar[MapError]
NODE_TYPE_UNSPECIFIED: NodeType
NODE_TYPE_HUB: NodeType
NODE_TYPE_MIDDLE: NodeType
NODE_TYPE_ZONE: NodeType
NODE_TYPE_INTRA_INPUT: NodeType
NODE_TYPE_INTRA_MID: NodeType
NODE_TYPE_INTRA_OUTPUT: NodeType
NODE_EVENT_UNSPECIFIED: NodeEvent
NODE_EVENT_CREATED: NodeEvent
NODE_EVENT_UPDATED: NodeEvent
NODE_EVENT_DELETED: NodeEvent
NODE_EVENT_TYPE_UNSPECIFIED: NodeEventType
NODE_EVENT_TYPE_INTERNAL: NodeEventType
NODE_EVENT_TYPE_EXTERNAL: NodeEventType
NODE_ERROR_UNSPECIFIED: NodeError
NODE_ERROR_DATABASE: NodeError
NODE_ERROR_REDIS: NodeError
NODE_ERROR_KAFKA: NodeError
PATH_EVENT_UNSPECIFIED: PathEvent
PATH_EVENT_CREATED: PathEvent
PATH_EVENT_UPDATED: PathEvent
PATH_EVENT_DELETED: PathEvent
ZONE_FILTER_EVENT_UNSPECIFIED: ZoneFilterEvent
ZONE_FILTER_EVENT_CREATED: ZoneFilterEvent
ZONE_FILTER_EVENT_UPDATED: ZoneFilterEvent
ZONE_FILTER_EVENT_DELETED: ZoneFilterEvent
ORDER_TAG_FILTER_EVENT_UNSPECIFIED: OrderTagFilterEvent
ORDER_TAG_FILTER_EVENT_CREATED: OrderTagFilterEvent
ORDER_TAG_FILTER_EVENT_UPDATED: OrderTagFilterEvent
ORDER_TAG_FILTER_EVENT_DELETED: OrderTagFilterEvent
OUTPUT_NODE_EVENT_UNSPECIFIED: OutputNodeEvent
OUTPUT_NODE_EVENT_CREATED: OutputNodeEvent
OUTPUT_NODE_EVENT_UPDATED: OutputNodeEvent
OUTPUT_NODE_EVENT_DELETED: OutputNodeEvent
MAP_EVENT_UNSPECIFIED: MapEvent
MAP_EVENT_CREATED: MapEvent
MAP_EVENT_UPDATED: MapEvent
MAP_EVENT_DELETED: MapEvent
MAP_ERROR_UNSPECIFIED: MapError
MAP_ERROR_GENERATE: MapError
MAP_ERROR_STORE: MapError
MAP_ERROR_PUBLISH: MapError

class SortNode(_message.Message):
    __slots__ = ("id", "real_id", "hub_id", "name", "type", "system_id", "rejection_criteria", "compat_id", "node_event", "error", "retry_count", "retry_datetime")
    ID_FIELD_NUMBER: _ClassVar[int]
    REAL_ID_FIELD_NUMBER: _ClassVar[int]
    HUB_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    REJECTION_CRITERIA_FIELD_NUMBER: _ClassVar[int]
    COMPAT_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_EVENT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    RETRY_COUNT_FIELD_NUMBER: _ClassVar[int]
    RETRY_DATETIME_FIELD_NUMBER: _ClassVar[int]
    id: int
    real_id: int
    hub_id: int
    name: str
    type: NodeType
    system_id: str
    rejection_criteria: int
    compat_id: int
    node_event: NodeEvent
    error: NodeError
    retry_count: int
    retry_datetime: int
    def __init__(self, id: _Optional[int] = ..., real_id: _Optional[int] = ..., hub_id: _Optional[int] = ..., name: _Optional[str] = ..., type: _Optional[_Union[NodeType, str]] = ..., system_id: _Optional[str] = ..., rejection_criteria: _Optional[int] = ..., compat_id: _Optional[int] = ..., node_event: _Optional[_Union[NodeEvent, str]] = ..., error: _Optional[_Union[NodeError, str]] = ..., retry_count: _Optional[int] = ..., retry_datetime: _Optional[int] = ...) -> None: ...

class SortPath(_message.Message):
    __slots__ = ("source_node_id", "destination_node_id", "id", "hub_id", "system_id", "distance", "rejection_conditions", "zone_filters", "label", "zone_filter_refs", "order_tag_filter_refs", "path_event")
    SOURCE_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    HUB_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    REJECTION_CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    ZONE_FILTERS_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    ZONE_FILTER_REFS_FIELD_NUMBER: _ClassVar[int]
    ORDER_TAG_FILTER_REFS_FIELD_NUMBER: _ClassVar[int]
    PATH_EVENT_FIELD_NUMBER: _ClassVar[int]
    source_node_id: int
    destination_node_id: int
    id: int
    hub_id: int
    system_id: str
    distance: int
    rejection_conditions: int
    zone_filters: _containers.RepeatedScalarFieldContainer[int]
    label: str
    zone_filter_refs: _containers.RepeatedCompositeFieldContainer[PathZoneFilter]
    order_tag_filter_refs: _containers.RepeatedCompositeFieldContainer[PathOrderTagFilter]
    path_event: PathEvent
    def __init__(self, source_node_id: _Optional[int] = ..., destination_node_id: _Optional[int] = ..., id: _Optional[int] = ..., hub_id: _Optional[int] = ..., system_id: _Optional[str] = ..., distance: _Optional[int] = ..., rejection_conditions: _Optional[int] = ..., zone_filters: _Optional[_Iterable[int]] = ..., label: _Optional[str] = ..., zone_filter_refs: _Optional[_Iterable[_Union[PathZoneFilter, _Mapping]]] = ..., order_tag_filter_refs: _Optional[_Iterable[_Union[PathOrderTagFilter, _Mapping]]] = ..., path_event: _Optional[_Union[PathEvent, str]] = ...) -> None: ...

class PathZoneFilter(_message.Message):
    __slots__ = ("zone_id", "zone_type")
    ZONE_ID_FIELD_NUMBER: _ClassVar[int]
    ZONE_TYPE_FIELD_NUMBER: _ClassVar[int]
    zone_id: int
    zone_type: str
    def __init__(self, zone_id: _Optional[int] = ..., zone_type: _Optional[str] = ...) -> None: ...

class PathOrderTagFilter(_message.Message):
    __slots__ = ("order_tag_id", "strategy")
    ORDER_TAG_ID_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_FIELD_NUMBER: _ClassVar[int]
    order_tag_id: int
    strategy: str
    def __init__(self, order_tag_id: _Optional[int] = ..., strategy: _Optional[str] = ...) -> None: ...

class SortMap(_message.Message):
    __slots__ = ("zone_id", "zone_node_id", "source_node_id", "destination_node_id", "system_id", "distance", "adjusted_distance", "rejection_conditions", "label", "map_event")
    ZONE_ID_FIELD_NUMBER: _ClassVar[int]
    ZONE_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    ADJUSTED_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    REJECTION_CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    MAP_EVENT_FIELD_NUMBER: _ClassVar[int]
    zone_id: int
    zone_node_id: int
    source_node_id: int
    destination_node_id: int
    system_id: str
    distance: int
    adjusted_distance: int
    rejection_conditions: int
    label: str
    map_event: MapEvent
    def __init__(self, zone_id: _Optional[int] = ..., zone_node_id: _Optional[int] = ..., source_node_id: _Optional[int] = ..., destination_node_id: _Optional[int] = ..., system_id: _Optional[str] = ..., distance: _Optional[int] = ..., adjusted_distance: _Optional[int] = ..., rejection_conditions: _Optional[int] = ..., label: _Optional[str] = ..., map_event: _Optional[_Union[MapEvent, str]] = ...) -> None: ...

class ZoneFilter(_message.Message):
    __slots__ = ("id", "system_id", "hub_id", "source_id", "destination_id", "zone_id", "ref_reject_condition_id", "zone_type", "zone_filter_event")
    ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    HUB_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_ID_FIELD_NUMBER: _ClassVar[int]
    ZONE_ID_FIELD_NUMBER: _ClassVar[int]
    REF_REJECT_CONDITION_ID_FIELD_NUMBER: _ClassVar[int]
    ZONE_TYPE_FIELD_NUMBER: _ClassVar[int]
    ZONE_FILTER_EVENT_FIELD_NUMBER: _ClassVar[int]
    id: int
    system_id: str
    hub_id: int
    source_id: int
    destination_id: int
    zone_id: int
    ref_reject_condition_id: int
    zone_type: str
    zone_filter_event: ZoneFilterEvent
    def __init__(self, id: _Optional[int] = ..., system_id: _Optional[str] = ..., hub_id: _Optional[int] = ..., source_id: _Optional[int] = ..., destination_id: _Optional[int] = ..., zone_id: _Optional[int] = ..., ref_reject_condition_id: _Optional[int] = ..., zone_type: _Optional[str] = ..., zone_filter_event: _Optional[_Union[ZoneFilterEvent, str]] = ...) -> None: ...

class OrderTagFilter(_message.Message):
    __slots__ = ("id", "system_id", "hub_id", "source_id", "destination_id", "order_tag_id", "strategy", "order_tag_filter_event")
    ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    HUB_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_TAG_ID_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_FIELD_NUMBER: _ClassVar[int]
    ORDER_TAG_FILTER_EVENT_FIELD_NUMBER: _ClassVar[int]
    id: int
    system_id: str
    hub_id: int
    source_id: int
    destination_id: int
    order_tag_id: int
    strategy: str
    order_tag_filter_event: OrderTagFilterEvent
    def __init__(self, id: _Optional[int] = ..., system_id: _Optional[str] = ..., hub_id: _Optional[int] = ..., source_id: _Optional[int] = ..., destination_id: _Optional[int] = ..., order_tag_id: _Optional[int] = ..., strategy: _Optional[str] = ..., order_tag_filter_event: _Optional[_Union[OrderTagFilterEvent, str]] = ...) -> None: ...

class OutputNode(_message.Message):
    __slots__ = ("id", "system_id", "hub_id", "output_hub_id", "zone_id", "zone_type", "output_node_event")
    ID_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    HUB_ID_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_HUB_ID_FIELD_NUMBER: _ClassVar[int]
    ZONE_ID_FIELD_NUMBER: _ClassVar[int]
    ZONE_TYPE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_NODE_EVENT_FIELD_NUMBER: _ClassVar[int]
    id: int
    system_id: str
    hub_id: int
    output_hub_id: int
    zone_id: int
    zone_type: str
    output_node_event: OutputNodeEvent
    def __init__(self, id: _Optional[int] = ..., system_id: _Optional[str] = ..., hub_id: _Optional[int] = ..., output_hub_id: _Optional[int] = ..., zone_id: _Optional[int] = ..., zone_type: _Optional[str] = ..., output_node_event: _Optional[_Union[OutputNodeEvent, str]] = ...) -> None: ...

class SortNodeEvents(_message.Message):
    __slots__ = ("system_id", "type", "node", "path", "zoneFilter", "outputNode", "orderTagFilters")
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NODE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    ZONEFILTER_FIELD_NUMBER: _ClassVar[int]
    OUTPUTNODE_FIELD_NUMBER: _ClassVar[int]
    ORDERTAGFILTERS_FIELD_NUMBER: _ClassVar[int]
    system_id: str
    type: NodeEventType
    node: _containers.RepeatedCompositeFieldContainer[SortNode]
    path: _containers.RepeatedCompositeFieldContainer[SortPath]
    zoneFilter: _containers.RepeatedCompositeFieldContainer[ZoneFilter]
    outputNode: _containers.RepeatedCompositeFieldContainer[OutputNode]
    orderTagFilters: _containers.RepeatedCompositeFieldContainer[OrderTagFilter]
    def __init__(self, system_id: _Optional[str] = ..., type: _Optional[_Union[NodeEventType, str]] = ..., node: _Optional[_Iterable[_Union[SortNode, _Mapping]]] = ..., path: _Optional[_Iterable[_Union[SortPath, _Mapping]]] = ..., zoneFilter: _Optional[_Iterable[_Union[ZoneFilter, _Mapping]]] = ..., outputNode: _Optional[_Iterable[_Union[OutputNode, _Mapping]]] = ..., orderTagFilters: _Optional[_Iterable[_Union[OrderTagFilter, _Mapping]]] = ...) -> None: ...

class SortMapEvents(_message.Message):
    __slots__ = ("system_id", "sortmap")
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    SORTMAP_FIELD_NUMBER: _ClassVar[int]
    system_id: str
    sortmap: _containers.RepeatedCompositeFieldContainer[SortMap]
    def __init__(self, system_id: _Optional[str] = ..., sortmap: _Optional[_Iterable[_Union[SortMap, _Mapping]]] = ...) -> None: ...

class SortMapGenerate(_message.Message):
    __slots__ = ("system_id", "zone_node", "path", "sort_map", "map_error", "version", "retry_count", "retry_datetime")
    SYSTEM_ID_FIELD_NUMBER: _ClassVar[int]
    ZONE_NODE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    SORT_MAP_FIELD_NUMBER: _ClassVar[int]
    MAP_ERROR_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    RETRY_COUNT_FIELD_NUMBER: _ClassVar[int]
    RETRY_DATETIME_FIELD_NUMBER: _ClassVar[int]
    system_id: str
    zone_node: SortNode
    path: _containers.RepeatedCompositeFieldContainer[SortPath]
    sort_map: _containers.RepeatedCompositeFieldContainer[SortMap]
    map_error: MapError
    version: int
    retry_count: int
    retry_datetime: int
    def __init__(self, system_id: _Optional[str] = ..., zone_node: _Optional[_Union[SortNode, _Mapping]] = ..., path: _Optional[_Iterable[_Union[SortPath, _Mapping]]] = ..., sort_map: _Optional[_Iterable[_Union[SortMap, _Mapping]]] = ..., map_error: _Optional[_Union[MapError, str]] = ..., version: _Optional[int] = ..., retry_count: _Optional[int] = ..., retry_datetime: _Optional[int] = ...) -> None: ...

class IntraCachingPathCondition(_message.Message):
    __slots__ = ("destination_id", "reject_conditions")
    DESTINATION_ID_FIELD_NUMBER: _ClassVar[int]
    REJECT_CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    destination_id: int
    reject_conditions: int
    def __init__(self, destination_id: _Optional[int] = ..., reject_conditions: _Optional[int] = ...) -> None: ...

class IntraCachingPathConditionList(_message.Message):
    __slots__ = ("paths",)
    PATHS_FIELD_NUMBER: _ClassVar[int]
    paths: _containers.RepeatedCompositeFieldContainer[IntraCachingPathCondition]
    def __init__(self, paths: _Optional[_Iterable[_Union[IntraCachingPathCondition, _Mapping]]] = ...) -> None: ...

class IntraCachingOutputNode(_message.Message):
    __slots__ = ("zone_id",)
    ZONE_ID_FIELD_NUMBER: _ClassVar[int]
    zone_id: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, zone_id: _Optional[_Iterable[int]] = ...) -> None: ...
