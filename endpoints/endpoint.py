"""Main endpoint of the API, handling CRUD based on Schema properties.

"""
from flask_restful import Resource
import pyodbc
from flask import request, jsonify
import marshmallow as MM
from marshmallow.decorators import post_dump
from globals import db_connection_settings, min_datetime, max_datetime
import re
import datetime
from flask_jwt_extended import get_jwt_identity
from collections import namedtuple, defaultdict
import uuid
import endpoints.references


class Default_Schema(MM.Schema):
    """
    Default Schema for an endpoint.

    All objects need to have these fields in order for time travelling and history to work.
    """
    ID = MM.fields.Integer(required=True, obprops=[
                           'excluded_patch', 'excluded_post'])
    UUID = MM.fields.UUID(required=True, obprops=[
                          'excluded_patch', 'excluded_post'])
    Created_By = MM.fields.UUID(required=True, obprops=[
                                'excluded_patch', 'excluded_post'])
    Created_Date = MM.fields.DateTime(format='iso', required=True, obprops=[
                                      'excluded_patch', 'excluded_post'])
    Modified_By = MM.fields.UUID(required=True, obprops=[
                                 'excluded_patch', 'excluded_post'])
    Modified_Date = MM.fields.DateTime(format='iso', required=True, obprops=[
                                       'excluded_patch', 'excluded_post'])

    @classmethod
    def fields_with_props(cls, prop):
        """
        Class method that returns all fields that have `prop`value in their obprops list.
        Returns a list
        """
        return list(map(lambda item: item[0], filter(lambda item: prop in item[1].metadata['obprops'], cls._declared_fields.items())))

    @classmethod
    def fields_without_props(cls, prop):
        """
        Class method that returns all fields that don't have `prop` value in their obprops list.
        Returns a list
        """
        return list(map(lambda item: item[0], filter(lambda item: prop not in item[1].metadata['obprops'], cls._declared_fields.items())))

    @post_dump()
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

    class Meta:
        ordered = True
        read_only = False
        references = {}


def row_to_dict(row):
    """
    Turns a row from pyodbc into a dictionary
    """
    return dict(zip([t[0] for t in row.cursor_description], row))


def handle_odbc_exception(odbc_ex):
    code = odbc_ex.args[0]
    return {"message": f"Database error [{code}] during handling of request", "detailed": str(odbc_ex)}


class Lineage_Endpoint(Resource):
    """
    A lineage is a list of all objects that have the same ID, ordered by modified date.
    This represents the history of an object in our database.
    """

    def __init__(self, read_schema, write_schema):
        self.read_schema = read_schema
        self.write_schema = write_schema

    def get(self, id):
        """
        GET endpoint for a single object's lineage
        """
        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            query = f"SELECT * FROM {self.read_schema.Meta.table} WHERE ID = ? ORDER BY Modified_Date DESC"
            
            all_objects = list(
                map(row_to_dict, cursor.execute(query, id)))

            for fieldname, reference in self.read_schema.Meta.references.items():
                all_objects = reference.merge_references(
                    all_objects, fieldname, connection)

            if len(all_objects) == 0:
                return {'message': f'Object with ID={id} not found'}, 404
            return(self.read_schema().dump(all_objects, many=True))

    def patch(self, id):
        """
        PATCH endpoint to add a new version to a lineage
        """
        if self.write_schema.Meta.read_only:
            return {'message': 'This endpoint is read-only'}, 403
        request_time = datetime.datetime.now()
        old_object = None
        
        # Check if the id exists
        with pyodbc.connect(db_connection_settings, autocommit=False) as connection:
            cursor = connection.cursor()
            query = f'SELECT TOP(1) * FROM {self.write_schema.Meta.table} WHERE ID = ? ORDER BY Modified_Date DESC'
            old_object = list(cursor.execute(query, id))
            if not(any(old_object)):
                return {'message': f'Object with ID={id} not found'}, 404
            else:
                old_object = row_to_dict(old_object[0])

            patch_schema = self.write_schema(
                exclude=self.write_schema.fields_with_props('excluded_patch'),
                unknown=MM.utils.RAISE,
                partial=True
            )
            try:
                changes = patch_schema.load(request.json)
            except MM.exceptions.ValidationError as err:
                return err.normalized_messages(), 400
                # Remove and store reference fields
            reference_lists = {}
            for ref_field in self.write_schema.Meta.references:
                if ref_field in changes:
                    reference_lists[ref_field] = changes.pop(ref_field)
            
            # Merge the changes into a new object and set correct values
            new_object = {**old_object, **changes}

            old_uuid = new_object.pop('UUID')
            new_object['Modified_Date'] = request_time
            new_object['Modified_By'] = get_jwt_identity()['UUID']
            column_names, values = tuple(zip(*new_object.items()))
            parameter_marks = ', '.join(['?'] * len(column_names))
            
            # Even tough this is a 'PATCH' endpoint we create a new row in order to preserve history
            query = f'''INSERT INTO {self.write_schema.Meta.table} ({', '.join(column_names)}) OUTPUT inserted.UUID VALUES ({parameter_marks})'''
            try:
                cursor.execute(query, *values)
            except pyodbc.IntegrityError as e:
                return {'message': 'Integrity error on this request, check wether the reference keys are valid.'}, 400
            except pyodbc.DatabaseError as e:
                return handle_odbc_exception(e), 500
            new_object['UUID'] = cursor.fetchone()[0]

            # Get the old references to recreate
            # if field not in reference_list -> get old ones
            # else use new ones
            for ref_field in self.write_schema.Meta.references:
                ref = self.write_schema.Meta.references[ref_field]
                if not ref_field in reference_lists:
                    ref.copy_references(old_object, new_object, connection)
                else:
                    ref.store_references(new_object, reference_lists[ref_field], connection)

            connection.commit()
            return self.write_schema().dump(new_object)


class List_Endpoint(Resource):
    """
    A list of all lineages in the table. Represented by the latests version in the lineage.
    """

    def __init__(self, read_schema, write_schema):
        self.read_schema = read_schema
        self.write_schema = write_schema

    def get(self):
        query = f"""
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (
                PARTITION BY [ID]
                ORDER BY [Modified_Date] DESC) [RowNumber]
                FROM {self.read_schema.Meta.table}) T
            WHERE RowNumber = 1 AND UUID != '00000000-0000-0000-0000-000000000000'
            """
        filters = request.args
        filter_values = []
        if filters:
            invalids = [
                f for f in filters if f not in self.read_schema.fields_without_props('reference')]
            if invalids:
                return {'message': f"Filter(s) '{' '.join(invalids)}' invalid for this endpoint. Valid filters: '{', '.join(self.read_schema.fields_without_props('reference'))}''"}, 403
            for f in filters:
                query += f' AND {f} = ?'
                filter_values.append(filters[f])
        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            all_objects = list(
                map(row_to_dict, cursor.execute(query, *filter_values)))

            for fieldname, reference in self.read_schema.Meta.references.items():
                all_objects = reference.merge_references(
                    all_objects, fieldname, connection)

            # Validation does not happen on dump
            return(self.read_schema().dump(all_objects, many=True))

    def post(self):
        """
        Add a new object the table. Starting a new lineage.
        """
        if self.write_schema.Meta.read_only or self.read_schema.Meta.read_only:
            return {'message': 'This endpoint is read-only'}, 403
        request_time = datetime.datetime.now()
        with pyodbc.connect(db_connection_settings, autocommit=False) as connection:
            cursor = connection.cursor()
            if request.json is None:
                return {'message': 'Request data empty'}, 400
            post_schema = self.write_schema(
                exclude=self.write_schema.fields_with_props('excluded_post'),
                unknown=MM.utils.RAISE
            )
            try:
                new_object = post_schema.load(request.json)
            except MM.exceptions.ValidationError as err:
                return err.normalized_messages(), 400

            # Remove and store reference field
            reference_lists = {}
            for ref_field in self.write_schema.Meta.references:
                if ref_field in new_object:
                    reference_lists[ref_field] = new_object.pop(ref_field)

            new_object['Created_By'] = get_jwt_identity()['UUID']
            new_object['Created_Date'] = request_time
            new_object['Modified_Date'] = new_object['Created_Date']
            new_object['Modified_By'] = new_object['Created_By']

            column_names, values = tuple(zip(*new_object.items()))
            parameter_marks = ', '.join(['?'] * len(column_names))
            query = f'''INSERT INTO {self.write_schema.Meta.table} ({', '.join(column_names)}) OUTPUT inserted.UUID, inserted.ID VALUES ({parameter_marks})'''
            try:
                cursor.execute(query, *values)
            except pyodbc.IntegrityError as e:
                return {'message': 'Integrity error on this request, check wether the reference keys are valid.'}, 400
            except pyodbc.DatabaseError as e:
                return handle_odbc_exception(e), 500
            output = cursor.fetchone()
            new_object['UUID'] = output[0]
            new_object['ID'] = output[1]

            for ref_field in reference_lists:
                self.write_schema.Meta.references[ref_field].store_references(
                    new_object, reference_lists[ref_field], connection)

            connection.commit()
            
            return self.write_schema().dump(new_object), 201


class Version_Endpoint(Resource):
    """
    This resource works on the single database rows, which are definied by their UUID field.
    This can be used to get a specific version of an object.
    """

    def __init__(self, read_schema, write_schema):
        self.read_schema = read_schema
        self.write_schema = write_schema

    def get(self, uuid):
        """
        GET endpoint based on UUID to get a specific version
        """
        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            query = f"SELECT * FROM {self.read_schema.Meta.table} WHERE UUID = ?"
            all_objects = list(
                map(row_to_dict, cursor.execute(query, uuid)))

            if not(any(all_objects)):
                return {'message': f'Object with UUID={uuid} not found'}, 404

            for fieldname, reference in self.read_schema.Meta.references.items():
                all_objects = reference.merge_references(
                    all_objects, fieldname, connection)

            return(self.read_schema().dump(all_objects[0]))