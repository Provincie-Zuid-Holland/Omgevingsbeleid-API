# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import datetime
import re

import marshmallow as MM
import pyodbc
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource
from globals import (db_connection_settings, max_datetime, min_datetime,
                     null_uuid, row_to_dict)

from Endpoints.base_schema import Base_Schema
from Endpoints.errors import (handle_integrity_exception,
                              handle_odbc_exception,
                              handle_validation_exception)
from Endpoints.references import merge_references, store_references

# TODO:
# - Write tests for reference objects
# - Add status validation
# - Add version on UUID
# - Add valid endpoint


def save_object(new_object, schema, cursor):
    """Saves an object to a table, retrieves and stores the generated values and return the object.

    Args:
        new_object (dict): The object to be stored 
        schema (marshmallow.Schema): The schema of the object
        cursor (pyodbc.cursor): A cursor with an active database connection

    Returns:
        dict: The object that was stored, new values filled in
    """

    references = schema.fields_with_props('referencelist')
    reference_cache = {}
    for ref in references:
        if ref in new_object:
            reference_cache[ref] = new_object.pop(ref)

    column_names, values = tuple(zip(*new_object.items()))
    parameter_marks = ', '.join(['?'] * len(column_names))
    query = f'''INSERT INTO {schema.Meta.table} ({', '.join(column_names)}) OUTPUT inserted.UUID, inserted.ID VALUES ({parameter_marks})'''
    cursor.execute(query, *values)

    output = cursor.fetchone()
    new_object['UUID'] = output[0]
    new_object['ID'] = output[1]

    for ref in reference_cache:
        new_object[ref] = reference_cache[ref]

    new_object = store_references(new_object, schema, cursor)

    # Up to here we have stored the references, and the object itself
    included_fields = ', '.join(
        [field for field in schema().fields_without_props('referencelist')])
    retrieve_query = f'''SELECT {included_fields} FROM {schema.Meta.table} WHERE UUID = ?'''
    return get_objects(retrieve_query, [new_object['UUID']], schema(), cursor)[0]


def get_objects(query, query_args, schema, cursor):
    """Retrieves objects using a given query

    Args:
        query (string): Sql query to use
        query_args (list): Arguments to fill the query with (using '?' notation from PyODBC)
        schema (marshmallow.Schema): The schema of the object
        cursor (pyodbc.Cursor): A cursor with an active database connection

    Returns:
        list: A collection of objects that resulted out of the query
    """
    query_result = map(row_to_dict, cursor.execute(query, *query_args))
    
    # Load the objects to ensure validation5754c1ae-ef1a-4f64-90bc-6b50cd7025ad
    result_objecten = list(map(schema.load, query_result))
    result_objecten = schema.dump(result_objecten, many=True)

    for obj in result_objecten:
        obj = merge_references(obj, schema, cursor)

    return(result_objecten)


class Lineage(Resource):
    """
    A lineage is a list of all object that have the same ID, ordered by modified date.
    This represents the history of an object in our database.
    """

    def __init__(self, read_schema, write_schema):
        self.read_schema = read_schema
        self.write_schema = write_schema

    def get(self, id):
        """
        GET endpoint for a lineage.
        """
        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()

            # Retrieve all the fields we want to query
            included_fields = ', '.join(
                [field for field in self.read_schema().fields_without_props('referencelist')])

            query = f'SELECT {included_fields} FROM {self.read_schema().Meta.table} WHERE ID = ? ORDER BY Modified_Date DESC'

            return(get_objects(query, [id], self.read_schema(), cursor))

    def patch(self, id):
        """
        PATCH endpoint for a lineage.
        """
        if self.write_schema.Meta.read_only or self.read_schema.Meta.read_only:
            return {'message': 'This endpoint is read-only'}, 403

        if request.json is None:
            return {'message': 'Request data empty'}, 400

        patch_schema = self.write_schema(
            exclude=self.write_schema.fields_with_props('exluded_patch'),
            unknown=MM.RAISE,
            partial=True
        )

        request_time = datetime.datetime.now()

        with pyodbc.connect(db_connection_settings, autocommit=False) as connection:
            cursor = connection.cursor()

            old_object = None

            query = f'SELECT TOP(1) * FROM {self.write_schema.Meta.table} WHERE ID = ? ORDER BY Modified_Date DESC'

            old_object = list(cursor.execute(query, id))
            if not(any(old_object)):
                return {'message': f'Object with ID={id} not found'}, 404
            else:
                old_object = row_to_dict(old_object[0])

            try:
                changes = patch_schema.load(request.json)
            except MM.exceptions.ValidationError as e:
                return handle_validation_exception(e)

            # TODO: Add reference logic

            new_object = {**old_object, **changes}

            new_object.pop('UUID')
            new_object['Modified_Date'] = request_time
            new_object['Modified_By'] = get_jwt_identity()['UUID']

            try:
                new_object = save_object(
                    new_object, self.write_schema, cursor)
            except pyodbc.IntegrityError as e:
                return handle_integrity_exception(e)
            except pyodbc.DatabaseError as e:
                return handle_odbc_exception(e)

            connection.commit()
            return new_object, 200


class List(Resource):
    """
    A list of all the different lineages available in the database, 
    showing the latests version of each object's lineage.
    """

    def __init__(self, read_schema, write_schema):
        self.read_schema = read_schema
        self.write_schema = write_schema

    def get(self):
        """
        GET endpoint for a list of objects, shows the last object for each lineage
        """

        # Check the filters for this request
        filters = request.args
        if filters:
            invalids = [
                f for f in filters if f not in self.read_schema().fields_without_props('referencelist')]
            if invalids:
                return {'message': f"Filter(s) '{' '.join(invalids)}' invalid for this endpoint. Valid filters: '{', '.join(self.read_schema().fields_without_props('referencelist'))}''"}, 403

        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()

            # Placeholder for arguments to filter
            query_args = None
            # Retrieve all the fields we want to query
            included_fields = ', '.join(
                [field for field in self.read_schema().fields_without_props('referencelist')])

            query = f'SELECT {included_fields} FROM (SELECT {included_fields}, ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] FROM {self.read_schema().Meta.table}) T WHERE RowNumber = 1'

            # No arguments for the default query
            query_args = []

            if filters:
                query += ' AND '+ 'AND '.join(f'{key} = ? ' for key in filters)
                query_args = [filters[key] for key in filters]

            query += ' ORDER BY Modified_Date DESC'
            return(get_objects(query, query_args, self.read_schema(), cursor))

    def post(self):
        """
        POST endpoint for this object.
        """
        if self.write_schema.Meta.read_only or self.read_schema.Meta.read_only:
            return {'message': 'This endpoint is read-only'}, 403

        if request.json is None:
            return {'message': 'Request data empty'}, 400

        post_schema = self.write_schema(
            exclude=self.write_schema.fields_with_props(
                'excluded_post'),
            unknown=MM.utils.RAISE)

        request_time = datetime.datetime.now()

        with pyodbc.connect(db_connection_settings, autocommit=False) as connection:
            cursor = connection.cursor()

            try:
                new_object = post_schema.load(request.get_json())
            except MM.exceptions.ValidationError as e:
                return handle_validation_exception(e), 400

            new_object['Created_By'] = get_jwt_identity()['UUID']
            new_object['Created_Date'] = request_time
            new_object['Modified_Date'] = new_object['Created_Date']
            new_object['Modified_By'] = new_object['Created_By']

            try:
                new_object = save_object(
                    new_object, self.write_schema, cursor)
            except pyodbc.IntegrityError as e:
                return handle_integrity_exception(e), 400
            except pyodbc.DatabaseError as e:
                return handle_odbc_exception(e), 500
            except MM.exceptions.ValidationError as e:
                return handle_validation_exception(e), 400

            connection.commit()
            return new_object, 201
