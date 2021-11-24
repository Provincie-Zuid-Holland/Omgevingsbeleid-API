# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import datetime
import re

import marshmallow as MM
from marshmallow.utils import pprint
from Endpoints.data_manager import DataManager
from globals import (
    db_connection_settings,
    max_datetime,
    min_datetime,
    null_uuid,
    row_to_dict,
)
from Endpoints.references import UUID_Reference
from Models.gebruikers import Gebruikers_Schema
import uuid


class Short_Base_Schema(MM.Schema):
    """
    Schema that defines fields we expect from every object in order to specify a version and lineage
    """

    ID = MM.fields.Integer(
        search_field="Keyword", obprops=["excluded_patch", "excluded_post", "short"]
    )
    UUID = MM.fields.UUID(
        required=True, obprops=["excluded_patch", "excluded_post", "short"]
    )

    class Meta:
        manager = DataManager
        ordered = True
        read_only = False
        base_references = {
            "Modified_By": UUID_Reference("Gebruikers", Gebruikers_Schema),
            "Created_By": UUID_Reference("Gebruikers", Gebruikers_Schema),
        }
        references = {}
        unknown = MM.RAISE
        # (field_name, valid_value)
        status_conf = None
        graph_conf = None
        geo_searchable = None

    def minmax_datetime(self, data):
        if (
            "Begin_Geldigheid" in data
            and data["Begin_Geldigheid"]
            == min_datetime.replace(tzinfo=datetime.timezone.utc).isoformat()
        ):
            data["Begin_Geldigheid"] = None
        if (
            "Eind_Geldigheid" in data
            and data["Eind_Geldigheid"]
            == max_datetime.replace(tzinfo=datetime.timezone.utc).isoformat()
        ):
            data["Eind_Geldigheid"] = None
        return data

    @MM.post_dump(pass_many=True)
    def minmax_datetime_many(self, data, many):
        if many:
            return list(map(self.minmax_datetime, data))
        else:
            return self.minmax_datetime(data)

    @MM.post_dump()
    def uppercase(self, dumped, many):
        """
        Ensure UUID's are uppercase.
        """
        for field in dumped:
            try:
                uuid.UUID(dumped[field])
                dumped[field] = dumped[field].upper()
            except:
                pass
        return dumped

    @MM.post_dump()
    def zulu_time(self, dumped, many):
        """
        Ensure UTC times have Zulu notation
        """
        for field in dumped:
            if isinstance(self.fields[field], MM.fields.DateTime):
                if dumped[field]:
                    dumped[field] = dumped[field] + "Z"
        return dumped

    @MM.post_dump()
    def remove_nill(self, dumped, many):
        """
        Change nill UUIDs to null
        """
        for field in dumped:
            if field not in ["UUID", "Created_By", "Modified_By"]:
                try:
                    if dumped[field] == null_uuid:
                        dumped[field] = None
                except:
                    pass
        return dumped

    @MM.pre_load()
    def stringify_datetimes(self, in_data, **kwargs):
        """
        Assures that datetimes from the database are loaded as isoformat
        """
        if in_data:
            for field in in_data:
                if isinstance(in_data[field], datetime.datetime):
                    in_data[field] = (
                        in_data[field].replace(tzinfo=datetime.timezone.utc).isoformat()
                    )
        return in_data

    @MM.post_load()
    def fill_missing_datetimes(self, in_data, **kwargs):
        """
        Save the min and max datetime on datetime fields that have None (null) as value
        """
        if in_data:
            if "Begin_Geldigheid" in in_data:
                if not in_data["Begin_Geldigheid"]:
                    in_data["Begin_Geldigheid"] = min_datetime.replace(
                        tzinfo=datetime.timezone.utc
                    )
            if "Eind_Geldigheid" in in_data:
                if not in_data["Eind_Geldigheid"]:
                    in_data["Eind_Geldigheid"] = max_datetime.replace(
                        tzinfo=datetime.timezone.utc
                    )
        return in_data

    @classmethod
    def fields_with_props(cls, props):
        """Class method that returns all fields that have `prop` value in their obprops list.

        Args:
            prop (str): The value to filter on

        Returns:
            list: The fields that have the prop in their obprops list
        """
        if type(props) != list:
            raise TypeError

        result = []
        for key, field in cls._declared_fields.items():
            fieldprops = field.metadata["obprops"]
            match = [prop for prop in fieldprops if prop in props]
            if match:
                result.append(key)
        return result

    @classmethod
    def fields_without_props(cls, props):
        """Class method that returns all fields that don't have `prop` value in their obprops list.

        Args:
            prop (list): List of strings to filter on

        Returns:
            list: The fields that do not have the prop in their obprops list
        """
        if type(props) != list:
            raise TypeError

        result = []
        for key, field in cls._declared_fields.items():
            fieldprops = field.metadata["obprops"]
            match = [prop for prop in fieldprops if prop in props]
            if not match:
                result.append(key)
        return result


class Base_Schema(Short_Base_Schema):
    """
    Schema that defines fields we expect from every object in order to build and keep a history.
    """

    Begin_Geldigheid = MM.fields.DateTime(
        format="iso", missing=min_datetime, allow_none=True, obprops=["short"]
    )
    Eind_Geldigheid = MM.fields.DateTime(
        format="iso", missing=max_datetime, allow_none=True, obprops=["short"]
    )
    Created_By = MM.fields.UUID(
        required=True, obprops=["excluded_patch", "excluded_post", "short"]
    )
    Created_Date = MM.fields.DateTime(
        format="iso",
        required=True,
        obprops=["excluded_patch", "excluded_post", "short"],
    )
    Modified_By = MM.fields.UUID(
        required=True, obprops=["excluded_patch", "excluded_post", "short"]
    )
    Modified_Date = MM.fields.DateTime(
        format="iso",
        required=True,
        obprops=["excluded_patch", "excluded_post", "short"],
    )
