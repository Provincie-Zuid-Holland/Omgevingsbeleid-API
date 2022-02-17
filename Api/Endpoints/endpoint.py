# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import datetime
from attr import validate
import marshmallow as MM
import pyodbc
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from Api.Endpoints.data_manager import DataManager
from Api.Endpoints.errors import (
    handle_UUID_does_not_exists,
    handle_empty,
    handle_empty_patch,
    handle_integrity_exception,
    handle_odbc_exception,
    handle_read_only,
    handle_validation_exception,
    handle_empty,
    handle_read_only,
    handle_UUID_does_not_exists,
    handle_ID_does_not_exists,
    handle_no_status,
    handle_integrity_exception,
    handle_odbc_exception,
    handle_validation_exception,
    handle_validation_filter_exception,
    handle_queryarg_exception,
)
from Api.Endpoints.references import (
    Reverse_ID_Reference,
    Reverse_UUID_Reference,
)
from Api.Endpoints.comparison import compare_objects


class QueryArgError(Exception):
    pass


def parse_query_args(q_args, valid_filters, filter_schema):
    """parses both filter values and pagination setting from the query arguments
    Args:
        q_args (Mapping): the query arguments (retrieved from request.args)
        valid_filters (List): Valid fields to filter on
        filter_schema (MM.Schema): Schema to validate filters on

    Returns:
        Dict: A dictionary that contains the filters (Dict, both any_filters and all_filters) and the Limit (Int) & Offset (Int)
    """
    parsed = {}
    parsed["limit"] = q_args.get("limit")
    parsed["offset"] = q_args.get("offset", 0)
    parsed["any_filters"] = None  # OR seperated filters
    parsed["all_filters"] = None  # AND seperated filters

    if parsed["limit"]:
        if int(parsed["limit"]) <= 0:
            raise QueryArgError(f"Limit must be > 0")

    if parsed["offset"] and int(parsed["offset"]) < 0:
        raise QueryArgError(f"Offset must be > 0")

    any_filters_strf = q_args.get("any_filters")
    if any_filters_strf:
        parsed["any_filters"] = dict(
            [tuple(filter.split(":")) for filter in any_filters_strf.split(",")]
        )
        invalids = [f for f in parsed["any_filters"].keys() if f not in valid_filters]
        if invalids:
            raise QueryArgError(
                f"Filter(s) '{' '.join(invalids)}' invalid for this endpoint. Valid filters: '{', '.join(valid_filters)}''"
            )
        parsed["any_filters"] = filter_schema.load(parsed["any_filters"])

    all_filters_strf = q_args.get("all_filters")
    if all_filters_strf:
        if any_filters_strf:
            raise QueryArgError(
                "Using both `all_filters` and `any_filters` is not supported"
            )
        parsed["all_filters"] = dict(
            [tuple(filter.split(":")) for filter in all_filters_strf.split(",")]
        )
        invalids = [f for f in parsed["all_filters"].keys() if f not in valid_filters]
        if invalids:
            raise QueryArgError(
                f"Filter(s) '{' '.join(invalids)}' invalid for this endpoint. Valid filters: '{', '.join(valid_filters)}''"
            )
        parsed["all_filters"] = filter_schema.load(parsed["all_filters"])

    return parsed


class Schema_Resource(Resource):
    """
    A base class that accepts a Marshmallow schema as configuration
    """

    def __init__(self, schema):
        self.schema = schema


class Lineage(Schema_Resource):
    """
    A lineage is a list of all object that have the same ID, ordered by modified date.
    This represents the history of an object in our database.
    """

    def get(self, id):
        """
        GET endpoint for a lineage.
        """
        try:
            q_args = parse_query_args(
                request.args,
                self.schema().fields_without_props(["referencelist"]),
                self.schema(partial=True),
            )
        except QueryArgError as e:
            # Invalid filter keys
            return handle_queryarg_exception(e)
        except MM.exceptions.ValidationError as e:
            # Invalid filter values
            return handle_validation_filter_exception(e)

        manager = self.schema.Meta.manager(self.schema)

        result_rows = manager.get_lineage(
            id, False, q_args["any_filters"], q_args["all_filters"], False
        )
        if result_rows:
            return result_rows, 200
        else:
            return handle_ID_does_not_exists(id)

    @jwt_required
    def patch(self, id):
        """
        PATCH endpoint for a lineage.
        """
        if self.schema.Meta.read_only:
            return handle_read_only()

        if request.json is None:
            return handle_empty()

        patch_schema = self.schema(
            exclude=self.schema.fields_with_props(["excluded_patch"]),
            unknown=MM.RAISE,
            partial=True,
        )

        request_time = datetime.datetime.now()

        try:
            changes = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as e:
            return handle_validation_exception(e)

        manager = self.schema.Meta.manager(self.schema)

        old_object = manager._get_latest_for_ID(id, valid_only=False)

        if not old_object:
            return handle_ID_does_not_exists(id)

        all_references = {
            **self.schema.Meta.base_references,
            **self.schema.Meta.references,
        }

       
        # Rewrite inlined references in patch format
        for ref in all_references:
            if ref in old_object:
                # Remove reverse references
                if isinstance(
                    all_references[ref], Reverse_UUID_Reference
                ) or isinstance(all_references[ref], Reverse_ID_Reference):
                    old_object.pop(ref)
                elif old_object[ref]:
                    if type(old_object[ref]) is list:

                        old_object[ref] = list(
                            map(
                                lambda r: {
                                    "UUID": r["Object"]["UUID"],
                                    "Koppeling_Omschrijving": r[
                                        "Koppeling_Omschrijving"
                                    ],
                                }
                                if "Object" in r
                                else r,
                                old_object[ref],
                            )
                        )
                    else:
                        old_object[ref] = old_object[ref]["UUID"]

        old_object = self.schema(
            exclude=self.schema.fields_with_props(["calculated"])
        ).load(old_object)

        # Remove ID & UUID from changes and old object
        old_object.pop("UUID")
        _id = old_object.pop("ID")

        new_object = {**old_object, **changes}

        if new_object == old_object:
            return handle_empty_patch()

        new_object["ID"] = _id
        new_object["Modified_Date"] = request_time
        new_object["Modified_By"] = get_jwt_identity()["UUID"]

        if "Aanpassing_Op" in old_object and not "Aanpassing_Op" in changes:
            new_object.pop("Aanpassing_Op")

        try:
            saved_obj = manager.save(new_object)
            return saved_obj, 200
        except pyodbc.IntegrityError as e:
            return handle_integrity_exception(e)
        except pyodbc.DatabaseError as e:
            return handle_odbc_exception(e), 500
        except MM.exceptions.ValidationError as e:
            return handle_validation_exception(e)


class FullList(Schema_Resource):
    """
    A list of all the different lineages available in the database,
    showing the latests version of each object's lineage.
    """

    @jwt_required
    def get(self):
        """
        GET endpoint for a list of objects, shows the last object for each lineage
        """
        try:
            q_args = parse_query_args(
                request.args,
                self.schema().fields_without_props(["referencelist"]),
                self.schema(partial=True),
            )
        except QueryArgError as e:
            # Invalid filter keys
            return handle_queryarg_exception(e)
        except MM.exceptions.ValidationError as e:
            # Invalid filter values
            return handle_validation_filter_exception(e)

        manager = self.schema.Meta.manager(self.schema)
        result_rows = manager.get_all(
            False, q_args["any_filters"], q_args["all_filters"], True
        )

        return result_rows, 200

    @jwt_required
    def post(self):
        """
        POST endpoint for this object.
        """
        if self.schema.Meta.read_only:
            return handle_read_only()

        if request.json is None:
            return handle_empty()

        post_schema = self.schema(
            exclude=self.schema.fields_with_props(["excluded_post"]),
            unknown=MM.utils.RAISE,
        )

        request_time = datetime.datetime.now()

        try:
            new_object = post_schema.load(request.get_json())
        except MM.exceptions.ValidationError as e:
            return handle_validation_exception(e)

        new_object["Created_By"] = get_jwt_identity()["UUID"]
        new_object["Created_Date"] = request_time
        new_object["Modified_Date"] = new_object["Created_Date"]
        new_object["Modified_By"] = new_object["Created_By"]

        manager = self.schema.Meta.manager(self.schema)

        try:
            saved_obj = manager.save(new_object)
            return saved_obj, 201
        except pyodbc.IntegrityError as e:
            return handle_integrity_exception(e)
        except pyodbc.DatabaseError as e:
            return handle_odbc_exception(e), 500
        except MM.exceptions.ValidationError as e:
            return handle_validation_exception(e)


class ValidList(Schema_Resource):
    """
    A list of all the different lineages available in the database.
    The objects are filtered by their start and end date.
    If the object has a status conf that is also used to filter the objects.

    Not availabe if the schema's status_conf is None
    """

    def get(self):
        """
        GET endpoint for a list of objects, shows the last valid object for each lineage
        """
        try:
            q_args = parse_query_args(
                request.args,
                self.schema().fields_without_props(["referencelist"]),
                self.schema(partial=True),
            )
        except QueryArgError as e:
            # Invalid filter keys
            return handle_queryarg_exception(e)
        except MM.exceptions.ValidationError as e:
            # Invalid filter values
            return handle_validation_filter_exception(e)

        manager = self.schema.Meta.manager(self.schema)

        return manager.get_all(True, q_args["any_filters"], q_args["all_filters"], True)


class ValidLineage(Schema_Resource):
    """
    A lineage is a list of all object that have the same ID, ordered by modified date.
    This represents the history of an object valid states in our database.
    """

    def get(self, id):
        """
        GET endpoint for a lineage.
        """
        try:
            q_args = parse_query_args(
                request.args,
                self.schema().fields_without_props(["referencelist"]),
                self.schema(partial=True),
            )
        except QueryArgError as e:
            # Invalid filter keys
            return handle_queryarg_exception(e)
        except MM.exceptions.ValidationError as e:
            # Invalid filter values
            return handle_validation_filter_exception(e)

        manager = self.schema.Meta.manager(self.schema)
        result_rows = manager.get_lineage(
            id, True, q_args["any_filters"], q_args["all_filters"], False
        )
        if result_rows:
            return result_rows, 200
        else:
            return handle_ID_does_not_exists(id)


class SingleVersion(Schema_Resource):
    """
    This represents a single version of an object, identified by it's UUID.
    """

    def get(self, uuid):
        """
        Get endpoint for a single object
        """
        manager = self.schema.Meta.manager(self.schema)
        try:
            result = manager.get_single_on_UUID(uuid)
            if not result:
                return handle_UUID_does_not_exists(uuid)
            return result, 200
        except MM.exceptions.ValidationError as e:
            return handle_validation_exception(e), 500


class Changes(Schema_Resource):
    """
    This represents the changes between two objects, identified by their UUIDs.
    """

    def get(self, old_uuid, new_uuid):
        """
        Get endpoint for a single object
        """
        manager = self.schema.Meta.manager(self.schema)
        old_object = manager.get_single_on_UUID(old_uuid)
        new_object = manager.get_single_on_UUID(new_uuid)

        if not old_object:
            return handle_UUID_does_not_exists(old_uuid)
        if not new_object:
            return handle_UUID_does_not_exists(new_uuid)
        return (
            {
                "old": old_object,
                "changes": compare_objects(self.schema(), old_object, new_object),
            }
        ), 200
