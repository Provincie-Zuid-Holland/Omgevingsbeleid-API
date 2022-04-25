# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow as MM
import pytest

from Api.Endpoints.base_schema import Base_Schema


class Sample_Schema(Base_Schema):
    Title = MM.fields.String(obprops=["foo"])
    Description = MM.fields.String(obprops=["foo", "bar"])
    Owner = MM.fields.UUID(obprops=["baz"])


class TestSchema:
    def test_non_list(self):
        try:
            Sample_Schema.fields_with_props("foo")
            Sample_Schema.fields_without_props("foo")
        except TypeError as e:
            assert True
        else:
            pytest.fail(
                "Calling field selectors without a list should raise an exception")

    def test_fields_with_props(self):
        assert Sample_Schema.fields_with_props(
            ["foo"]) == ["Title", "Description"]
        assert Sample_Schema.fields_with_props(["foo", "baz"]) == [
            "Title",
            "Description",
            "Owner",
        ]
        assert Sample_Schema.fields_with_props([""]) == []
        assert Sample_Schema.fields_with_props(["bar"]) == ["Description"]

    def test_fields_without_props(self):
        assert Sample_Schema.fields_without_props(["foo"]) == [
            "ID",
            "UUID",
            "Begin_Geldigheid",
            "Eind_Geldigheid",
            "Created_By",
            "Created_Date",
            "Modified_By",
            "Modified_Date",
            "Owner",
        ]

        assert Sample_Schema.fields_without_props(["bla"]) == [
            "ID",
            "UUID",
            "Begin_Geldigheid",
            "Eind_Geldigheid",
            "Created_By",
            "Created_Date",
            "Modified_By",
            "Modified_Date",
            "Title",
            "Description",
            "Owner",
        ]

        assert Sample_Schema.fields_without_props(["bar", "baz"]) == [
            "ID",
            "UUID",
            "Begin_Geldigheid",
            "Eind_Geldigheid",
            "Created_By",
            "Created_Date",
            "Modified_By",
            "Modified_Date",
            "Title",
        ]
