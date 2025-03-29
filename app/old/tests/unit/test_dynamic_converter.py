from typing import Callable

import pytest

from app.dynamic.config.models import Api, Column, EndpointConfig, Field, IntermediateObject
from app.dynamic.converter import Converter, ObjectConverterData


class TestDynamicConverter:
    """
    Ensure dynamic column/field mapping works as expected with
    serializers and deserializers. Use a simple upper/lowercase func as
    example.
    """

    @pytest.fixture
    def converter(self):
        converter = Converter()
        converter.register_serializer("uppercase", lambda x: x.upper())
        converter.register_serializer("lowercase", lambda x: x.lower())
        return converter

    @pytest.fixture
    def intermediate_object(self):
        columns = {
            "Title": Column(
                id="Title",
                name="Title",
                type="str",
                deserializers=["uppercase"],
                serializers=["lowercase"],
            ),
            "Description": Column(
                id="Description",
                name="Description",
                type="str",
                deserializers=["lowercase"],
                serializers=["uppercase"],
            ),
        }
        fields = {
            "Title": Field(id="Title", column="Title", name="Title", type="str", optional=True),
            "Description": Field(
                id="Description",
                column="Description",
                name="Description",
                type="str",
                optional=True,
            ),
        }
        endpoint_configs = [
            EndpointConfig(prefix="/mock/api", resolver_id="mock_id", resolver_data={}),
        ]
        api = Api(id="1", object_type="test", endpoint_configs=endpoint_configs)
        return IntermediateObject(
            id="1",
            columns=columns,
            fields=fields,
            config={},
            api=api,
        )

    @pytest.fixture
    def object_converter_data(self, converter: Converter, intermediate_object: IntermediateObject):
        converter.build_for_object(intermediate_object)
        return converter._per_object_id[intermediate_object.id]

    def test_build_for_object(self, converter: Converter, intermediate_object: IntermediateObject):
        assert intermediate_object.id not in converter._per_object_id

        converter.build_for_object(intermediate_object)
        assert intermediate_object.id in converter._per_object_id

        object_converter_data = converter._per_object_id[intermediate_object.id]

        assert "Title" in object_converter_data._column_deserializers
        assert "Description" in object_converter_data._column_deserializers
        assert "Title" in object_converter_data._field_serializers
        assert "Description" in object_converter_data._field_serializers

        column_deserializer1 = object_converter_data._column_deserializers["Title"]
        assert column_deserializer1.field_name == "Title"
        assert isinstance(column_deserializer1.deserializers[0], Callable)

        column_deserializer2 = object_converter_data._column_deserializers["Description"]
        assert column_deserializer2.field_name == "Description"
        assert isinstance(column_deserializer2.deserializers[0], Callable)

        field_serializer1 = object_converter_data._field_serializers["Title"]
        assert field_serializer1.column_name == "Title"
        assert len(field_serializer1.serializers) == 1

        field_serializer2 = object_converter_data._field_serializers["Description"]
        assert field_serializer2.column_name == "Description"
        assert len(field_serializer2.serializers) == 1

    def test_object_converter_data_deserialize(self, object_converter_data: ObjectConverterData):
        database_data = {
            "Title": "hello world",
            "Description": "THIS IS A TEST",
        }
        expected_result = {
            "Title": "HELLO WORLD",
            "Description": "this is a test",
        }
        deserialized_data = object_converter_data.deserialize(database_data)
        assert deserialized_data == expected_result

    def test_object_converter_data_serialize(self, object_converter_data: ObjectConverterData):
        field_data = {
            "Title": "HELLO WORLD",
            "Description": "this is a test",
        }
        expected_result = {
            "Title": "hello world",
            "Description": "THIS IS A TEST",
        }
        serialized_data = object_converter_data.serialize(field_data)
        assert serialized_data == expected_result
