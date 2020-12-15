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

from Endpoints.errors import (handle_integrity_exception,
                              handle_odbc_exception,
                              handle_validation_exception)


def save_object(new_object, tn, cursor):
    column_names, values = tuple(zip(*new_object.items()))
    parameter_marks = ', '.join(['?'] * len(column_names))
    query = f'''INSERT INTO {tn} ({', '.join(column_names)}) OUTPUT inserted.UUID, inserted.ID VALUES ({parameter_marks})'''
    
    cursor.execute(query, *values)
    
    output = cursor.fetchone()
    new_object['UUID'] = output[0]
    new_object['ID'] = output[1]
    return new_object

class Base_Schema(MM.Schema):
    """
    Schema that defines fields we expect from every object in order to build and keep a history.
    """
    ID = MM.fields.Integer(search_field="Keyword", obprops=[
                           'excluded_patch', 'excluded_post'])
    UUID = MM.fields.UUID(required=True, obprops=[
                          'excluded_patch', 'excluded_post'])
    Begin_Geldigheid = MM.fields.DateTime(
        format='iso', missing=min_datetime, obprops=[])
    Eind_Geldigheid = MM.fields.DateTime(
        format='iso', missing=max_datetime, obprops=[])
    Created_By = MM.fields.UUID(required=True, obprops=[
                                'excluded_patch', 'excluded_post'])
    Created_Date = MM.fields.DateTime(format='iso', required=True, obprops=[
                                      'excluded_patch', 'excluded_post'])
    Modified_By = MM.fields.UUID(required=True, obprops=[
                                 'excluded_patch', 'excluded_post'])
    Modified_Date = MM.fields.DateTime(format='iso', required=True, obprops=[
                                       'excluded_patch', 'excluded_post'])

    def minmax_datetime(self, data):

        if 'Begin_Geldigheid' in data and data['Begin_Geldigheid'] == min_datetime.isoformat():
            data['Begin_Geldigheid'] = None
        if 'Eind_Geldigheid' in data and data['Eind_Geldigheid'] == max_datetime.isoformat():
            data['Eind_Geldigheid'] = None
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
    def remove_nill(self, dumped, many):
        """
        Change nill UUIDs to null
        """
        for field in dumped:
            if field != 'UUID':
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
        for field in in_data:
            if isinstance(in_data[field], datetime.datetime):
                in_data[field] = in_data[field].isoformat()
        return in_data

    @classmethod
    def fields_with_props(cls, prop):
        """
        Class method that returns all fields that have `prop`value in their obprops list.
        Returns a list
        """
        matched_fields = filter(
            lambda item: prop in item[1].metadata['obprops'], cls._declared_fields.items())
        return list(map(lambda item: item[1].attribute or item[0], matched_fields))

    @classmethod
    def fields_without_props(cls, prop):
        """
        Class method that returns all fields that don't have `prop` value in their obprops list.
        Returns a list
        """
        return list(map(lambda item: item[0], filter(lambda item: prop not in item[1].metadata['obprops'], cls._declared_fields.items())))

    class Meta:
        ordered = True
        read_only = False
        references = {}
        unknown = MM.RAISE


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
            included_fields = ', '.join([field for field in self.read_schema().fields])

            query = f'SELECT {included_fields} FROM {self.read_schema().Meta.table} WHERE ID = ? ORDER BY Modified_Date DESC'

            try:
                # Load the objects to ensure validation
                result_objecten = list(map(self.read_schema().load,
                                           map(row_to_dict, cursor.execute(query, id))))
            except MM.exceptions.ValidationError as e:
                return handle_validation_exception(e)

            if len(result_objecten) == 0:
                return {'message': f'Object with ID={id} not found'}, 404
            return(self.read_schema().dump(result_objecten, many=True))

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
                new_object = save_object(new_object, self.write_schema.Meta.table, cursor)
            except pyodbc.IntegrityError as e:
                return handle_integrity_exception(e)
            except pyodbc.DatabaseError as e:
                return handle_odbc_exception(e)

            connection.commit()
            return self.write_schema().dump(new_object), 200


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
        GET endpoint for a list
        """

        # Check the filters for this request
        filters = request.args
        if filters:
            invalids = [
                f for f in filters if f not in self.read_schema().fields_without_props('reference')]
            if invalids:
                return {'message': f"Filter(s) '{' '.join(invalids)}' invalid for this endpoint. Valid filters: '{', '.join(self.read_schema().fields_without_props('reference'))}''"}, 403

        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()

            # Placeholder for arguments to filter
            query_args = None
            # Retrieve all the fields we want to query
            included_fields = ', '.join([field for field in self.read_schema().fields])
            
            query = f'SELECT {included_fields} FROM {self.read_schema().Meta.table}'

            if filters:
                query += ' WHERE ' + \
                    ' AND '.join(f'{key} = ?' for key in filters)
                query_args = [filters[key] for key in filters]

            query += ' ORDER BY Modified_Date DESC'

            try:
                # Load the recieved objects to ensure validation
                if filters:
                    result_objecten = list(map(self.read_schema().load,
                                               map(row_to_dict, cursor.execute(query, query_args))))
                else:
                    result_objecten = list(map(self.read_schema().load,
                                               map(row_to_dict, cursor.execute(query))))

            except MM.exceptions.ValidationError as e:
                return handle_validation_exception(e)

            return(self.read_schema().dump(result_objecten, many=True))

    def post(self):
        """
        POST endpoint for this object.
        """
        if self.write_schema.Meta.read_only or self.read_schema.Meta.read_only:
            return {'message': 'This endpoint is read-only'}, 403

        if request.json is None:
                return {'message': 'Request data empty'}, 400

        post_schema = self.write_schema(
                exclude=self.write_schema.fields_with_props('excluded_post'),
                unknown=MM.utils.RAISE)

        request_time = datetime.datetime.now()

        with pyodbc.connect(db_connection_settings, autocommit=False) as connection:
            cursor = connection.cursor()

            try:
                new_object = post_schema.load(request.get_json())
            except MM.exceptions.ValidationError as e:
                return handle_validation_exception(e)

            # TODO: Add reference logic

            new_object['Created_By'] = get_jwt_identity()['UUID']
            new_object['Created_Date'] = request_time
            new_object['Modified_Date'] = new_object['Created_Date']
            new_object['Modified_By'] = new_object['Created_By']
            
            try:
                new_object = save_object(new_object, self.write_schema.Meta.table, cursor)
            except pyodbc.IntegrityError as e:
                return handle_integrity_exception(e)
            except pyodbc.DatabaseError as e:
                return handle_odbc_exception(e)

            connection.commit()
            return self.write_schema().dump(new_object), 201
