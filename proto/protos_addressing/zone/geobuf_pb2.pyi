from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Data(_message.Message):
    __slots__ = ("keys", "dimensions", "precision", "feature_collection", "feature", "geometry")
    class Feature(_message.Message):
        __slots__ = ("geometry", "id", "int_id", "values", "properties", "custom_properties")
        GEOMETRY_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        INT_ID_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        PROPERTIES_FIELD_NUMBER: _ClassVar[int]
        CUSTOM_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
        geometry: Data.Geometry
        id: str
        int_id: int
        values: _containers.RepeatedCompositeFieldContainer[Data.Value]
        properties: _containers.RepeatedScalarFieldContainer[int]
        custom_properties: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, geometry: _Optional[_Union[Data.Geometry, _Mapping]] = ..., id: _Optional[str] = ..., int_id: _Optional[int] = ..., values: _Optional[_Iterable[_Union[Data.Value, _Mapping]]] = ..., properties: _Optional[_Iterable[int]] = ..., custom_properties: _Optional[_Iterable[int]] = ...) -> None: ...
    class Geometry(_message.Message):
        __slots__ = ("type", "lengths", "coords", "geometries", "values", "custom_properties")
        class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            POINT: _ClassVar[Data.Geometry.Type]
            MULTIPOINT: _ClassVar[Data.Geometry.Type]
            LINESTRING: _ClassVar[Data.Geometry.Type]
            MULTILINESTRING: _ClassVar[Data.Geometry.Type]
            POLYGON: _ClassVar[Data.Geometry.Type]
            MULTIPOLYGON: _ClassVar[Data.Geometry.Type]
            GEOMETRYCOLLECTION: _ClassVar[Data.Geometry.Type]
        POINT: Data.Geometry.Type
        MULTIPOINT: Data.Geometry.Type
        LINESTRING: Data.Geometry.Type
        MULTILINESTRING: Data.Geometry.Type
        POLYGON: Data.Geometry.Type
        MULTIPOLYGON: Data.Geometry.Type
        GEOMETRYCOLLECTION: Data.Geometry.Type
        TYPE_FIELD_NUMBER: _ClassVar[int]
        LENGTHS_FIELD_NUMBER: _ClassVar[int]
        COORDS_FIELD_NUMBER: _ClassVar[int]
        GEOMETRIES_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        CUSTOM_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
        type: Data.Geometry.Type
        lengths: _containers.RepeatedScalarFieldContainer[int]
        coords: _containers.RepeatedScalarFieldContainer[int]
        geometries: _containers.RepeatedCompositeFieldContainer[Data.Geometry]
        values: _containers.RepeatedCompositeFieldContainer[Data.Value]
        custom_properties: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, type: _Optional[_Union[Data.Geometry.Type, str]] = ..., lengths: _Optional[_Iterable[int]] = ..., coords: _Optional[_Iterable[int]] = ..., geometries: _Optional[_Iterable[_Union[Data.Geometry, _Mapping]]] = ..., values: _Optional[_Iterable[_Union[Data.Value, _Mapping]]] = ..., custom_properties: _Optional[_Iterable[int]] = ...) -> None: ...
    class FeatureCollection(_message.Message):
        __slots__ = ("features", "values", "custom_properties")
        FEATURES_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        CUSTOM_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
        features: _containers.RepeatedCompositeFieldContainer[Data.Feature]
        values: _containers.RepeatedCompositeFieldContainer[Data.Value]
        custom_properties: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, features: _Optional[_Iterable[_Union[Data.Feature, _Mapping]]] = ..., values: _Optional[_Iterable[_Union[Data.Value, _Mapping]]] = ..., custom_properties: _Optional[_Iterable[int]] = ...) -> None: ...
    class Value(_message.Message):
        __slots__ = ("string_value", "double_value", "pos_int_value", "neg_int_value", "bool_value", "json_value")
        STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
        DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
        POS_INT_VALUE_FIELD_NUMBER: _ClassVar[int]
        NEG_INT_VALUE_FIELD_NUMBER: _ClassVar[int]
        BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
        JSON_VALUE_FIELD_NUMBER: _ClassVar[int]
        string_value: str
        double_value: float
        pos_int_value: int
        neg_int_value: int
        bool_value: bool
        json_value: str
        def __init__(self, string_value: _Optional[str] = ..., double_value: _Optional[float] = ..., pos_int_value: _Optional[int] = ..., neg_int_value: _Optional[int] = ..., bool_value: _Optional[bool] = ..., json_value: _Optional[str] = ...) -> None: ...
    KEYS_FIELD_NUMBER: _ClassVar[int]
    DIMENSIONS_FIELD_NUMBER: _ClassVar[int]
    PRECISION_FIELD_NUMBER: _ClassVar[int]
    FEATURE_COLLECTION_FIELD_NUMBER: _ClassVar[int]
    FEATURE_FIELD_NUMBER: _ClassVar[int]
    GEOMETRY_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedScalarFieldContainer[str]
    dimensions: int
    precision: int
    feature_collection: Data.FeatureCollection
    feature: Data.Feature
    geometry: Data.Geometry
    def __init__(self, keys: _Optional[_Iterable[str]] = ..., dimensions: _Optional[int] = ..., precision: _Optional[int] = ..., feature_collection: _Optional[_Union[Data.FeatureCollection, _Mapping]] = ..., feature: _Optional[_Union[Data.Feature, _Mapping]] = ..., geometry: _Optional[_Union[Data.Geometry, _Mapping]] = ...) -> None: ...
