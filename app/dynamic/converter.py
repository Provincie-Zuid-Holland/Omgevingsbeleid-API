from typing import Callable, Dict, List
from dataclasses import dataclass

from app.dynamic.config.models import IntermediateObject


@dataclass
class ColumnDeserialize:
    field_name: str
    deserializers: List[Callable]


@dataclass
class FieldSerialize:
    column_name: str
    serializers: List[Callable]


class ObjectConverterData:
    def __init__(
        self,
        column_deserializers: Dict[str, ColumnDeserialize],
        field_serializers: Dict[str, FieldSerialize],
    ):
        self._column_deserializers: Dict[str, ColumnDeserialize] = column_deserializers
        self._field_serializers: Dict[str, FieldSerialize] = field_serializers

    def deserialize(self, database_data: dict) -> dict:
        result_data: dict = {}
        for data_key, data_value in database_data.items():
            # If we do not know the column than it might be some extensions data
            # and we expect that extension to have fixed it already
            if not data_key in self._column_deserializers:
                result_data[data_key] = data_value
                continue

            column_deserializer = self._column_deserializers[data_key]
            new_value = data_value
            for deserializer in column_deserializer.deserializers:
                new_value = deserializer(new_value)

            result_data[column_deserializer.field_name] = new_value

        return result_data

    def serialize(self, field_data: dict) -> dict:
        result_data: dict = {}
        for data_key, data_value in field_data.items():
            # If we do not know the field than it might be some extensions data
            # and we do not store the extension data in the objects table
            if not data_key in self._field_serializers:
                continue

            field_serializer = self._field_serializers[data_key]
            new_value = data_value
            for serializer in field_serializer.serializers:
                new_value = serializer(new_value)

            result_data[field_serializer.column_name] = new_value

        return result_data


class Converter:
    def __init__(self):
        # These are all the registered serializers and validators
        # Serializers and Deserializers use the same set of functions
        self._serializers: Dict[str, Callable] = {}
        self._validators: Dict[str, Callable] = {}

        # This is a lookup for objects
        # Which is what actually is used in endpoints
        # ObjectID
        self._per_object_id: Dict[str, ObjectConverterData] = {}

    def register_serializer(self, id: str, function: Callable):
        if id in self._serializers:
            raise RuntimeError(f"Serializer ID '{id}' already exists")

        self._serializers[id] = function

    def register_validator(self, id: str, function: Callable):
        if id in self._validators:
            raise RuntimeError(f"Validator ID '{id}' already exists")

        self._validators[id] = function

    def deserialize_list(self, object_id: str, rows: List[dict]) -> List[dict]:
        return [self.deserialize(object_id, r) for r in rows]

    def deserialize(self, object_id: str, database_data: dict) -> dict:
        if not object_id in self._per_object_id:
            raise RuntimeError(f"No converter configured for object id: '{object_id}'")

        object_converter = self._per_object_id[object_id]
        return object_converter.deserialize(database_data)

    def serialize_list(self, object_id: str, rows: List[dict]) -> List[dict]:
        return [self.serialize(object_id, r) for r in rows]

    def serialize(self, object_id: str, field_data: dict) -> dict:
        if not object_id in self._per_object_id:
            raise RuntimeError(f"No converter configured for object id: '{object_id}'")

        object_converter = self._per_object_id[object_id]
        return object_converter.serialize(field_data)

    def build_for_object(self, object_itermediate: IntermediateObject):
        # Deserialize (column to field)
        column_deserializers: Dict[str, ColumnDeserialize] = {}
        field_serializers: Dict[str, FieldSerialize] = {}

        for field_id, field in object_itermediate.fields.items():
            if not field.column in object_itermediate.columns:
                raise RuntimeError(f"Missing column: '{field.column}'")
            column = object_itermediate.columns[field.column]

            # From database to field
            deserializer_functions: List[Callable] = []
            for deserializer_id in column.deserializers:
                if not deserializer_id in self._serializers:
                    raise RuntimeError(
                        f"Missing deserializer with id: '{deserializer_id}'"
                    )
                deserializer_functions.append(self._serializers[deserializer_id])
            column_deserializers[column.name] = ColumnDeserialize(
                field_name=field.name,
                deserializers=deserializer_functions,
            )

            # From field to database
            serializer_functions: List[Callable] = []
            for serializer_id in column.serializers:
                if not serializer_id in self._serializers:
                    raise RuntimeError(f"Missing serializer with id: '{serializer_id}'")
                serializer_functions.append(self._serializers[serializer_id])
            field_serializers[column.name] = FieldSerialize(
                column_name=column.name,
                serializers=serializer_functions,
            )

        self._per_object_id[object_itermediate.id] = ObjectConverterData(
            column_deserializers=column_deserializers,
            field_serializers=field_serializers,
        )
