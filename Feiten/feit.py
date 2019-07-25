import marshmallow as MM
import records
import pyodbc
from flask_restful import Resource
from flask import request, jsonify
import datetime
from flask_jwt_extended import get_jwt_identity
import pyodbc
from globals import db_connection_string, db_connection_settings
import json


def handle_odbc_exception(odbc_ex):
    code, desc = odbc_ex.args[0], odbc_ex.args[1]
    return {"message": f"Database error [{code}] during handling of request"}


def row_to_dict(row):
    return dict(zip([t[0] for t in row.cursor_description], row))


def objects_from_query(query):
    """
    Verkrijg alle objecten uit een table
    """
    db = records.Database(db_connection_string)
    return db.query(query)


class Feiten_Schema(MM.Schema):
    """
    Schema voor de standaard velden van een feit
    """
    ID = MM.fields.Integer()
    UUID = MM.fields.UUID(required=True)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.UUID(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.UUID(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)

    class Meta:
        ordered = True


class Link_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Omschrijving = MM.fields.Str(missing="")

    class Meta:
        ordered = True


def generate_fact(facts, fact_schema):
    """
    Turns a set of flat rows into a schema with nested relationships
    """
    schema = fact_schema()
    result = {}
    for fact in facts:
        fact = row_to_dict(fact)
        for field in schema.declared_fields:
            if f'fk_{field}' in fact or f'{field}_Omschrijving' in fact:
                try:
                    assert(
                        f'fk_{field}' in fact and f'{field}_Omschrijving' in fact)
                except AssertionError:
                    raise Exception(
                        f"Configuration for field '{field}' invalid, missing 'fk_{field}' or '{field}_Omschrijving' in database")
                link_object = {
                    'UUID': fact[f'fk_{field}'], 'Omschrijving': fact[f'{field}_Omschrijving']}
                if link_object['UUID'] or link_object['Omschrijving']:
                    if link_object['UUID'] != "00000000-0000-0000-0000-000000000000":
                        if field in result:
                            result[field].append(link_object)
                        else:
                            result[field] = [link_object]
    return(schema.dump(result))


def generate_rows(fact_schema, fact, fact_to_meta_field, excluded_fields):
    """
    Turns a schema with nested relationships into a set of flat rows
    """
    relationship_fields = [
        field for field in fact_schema.declared_fields if field not in excluded_fields]
    relationship_fields_max_len = max(
        map(lambda fieldname: len(fact[fieldname]), relationship_fields))
    result = []
    for i in range(relationship_fields_max_len):
        result.append({})
        for field in relationship_fields:
            try:
                linked = fact[field][i]
            except IndexError:
                linked = {"UUID": "00000000-0000-0000-0000-000000000000",
                          "Omschrijving": None}
            result[i][f'fk_{field}'] = linked['UUID']
            result[i][f'{field}_Omschrijving'] = linked['Omschrijving']
    return result

# GET /id -> Lineage X
# PATCH /id -> patch on last child
# GET / -> List X
# GET /UUID 
# POST / -> Add new X

def generate_allowed_fields(meta_schema, fact_schema, excluded_fields):
    """Generates a list of allowed fields for a meta and fact object combination"""
    possible_fields = list(
        {**meta_schema.declared_fields, **fact_schema.declared_fields}.keys())
    allowed_fields = [
        field for field in possible_fields if field not in excluded_fields]
    return allowed_fields


def generate_meta_insert(meta_tablename, meta_schema, excluded_create_fields):
    """
    generate an INSERT INTO query for Meta objects, includes an OUTPUT for UUID & ID.
    Returns a tuple (field_order, query)
    """
    meta_create_fields = ""
    meta_create_values = ""
    meta_field_order = []
    for field in meta_schema.declared_fields:
        if field not in excluded_create_fields:
            if meta_schema.declared_fields[field].attribute:
                meta_create_fields += f"[{field.attribute}], "
            else:
                meta_create_fields += f"[{field}], "
            meta_create_values += "?, "
            meta_field_order.append(field)
    meta_create_fields = meta_create_fields[:-2]
    meta_create_values = meta_create_values[:-2]
    return (meta_field_order, f'''INSERT INTO [{meta_tablename}] ({meta_create_fields}) OUTPUT inserted.UUID, inserted.ID VALUES ({meta_create_values})''')


def generate_fact_insert(linked_rows, fact_tablename, fact_schema, fact_to_meta_field, excluded_create_fields, excluded_fact_post_fields):
    """
    generate an INSERT INTO query for Fact objects
    Returns a tuple (field_order, query)
    """
    fact_create_fields = ""
    fact_create_values = ""
    all_fields = (list(linked_rows[0].keys()) + excluded_fact_post_fields)
    fact_field_order = [field for field in all_fields if field not in excluded_create_fields]
    if fact_to_meta_field in fact_schema.declared_fields:
        f2m_field = fact_schema.declared_fields[fact_to_meta_field]
        if f2m_field.attribute:
            fact_field_order.remove(fact_to_meta_field)
            fact_field_order.append(f2m_field.attribute)
    for field in fact_field_order:
        fact_create_fields += f"[{field}], "
        fact_create_values += "?, "
    fact_create_fields = fact_create_fields[:-2]
    fact_create_values = fact_create_values[:-2]
    return (fact_field_order, f'''INSERT INTO [{fact_tablename}] ({fact_create_fields}) VALUES ({fact_create_values})''')
        

class FeitenLineage(Resource):
    def __init__(self, meta_schema, meta_tablename, fact_schema, fact_tablename, fact_to_meta_field, read_schema)::
        self._meta_tablename = meta_tablename
        self._meta_schema = meta_schema
        self._fact_schema = fact_schema
        self._fact_to_meta_field_attr = fact_schema(
        ).declared_fields[fact_to_meta_field].attribute
        self._fact_to_meta_field = fact_to_meta_field
        self._fact_tablename = fact_tablename
        self._read_schema = read_schema

    def get(self, id):
        id_meta_query = f"SELECT * FROM {self._meta_tablename} WHERE UUID != '00000000-0000-0000-0000-000000000000' AND ID == ?"
        try:
            meta_objects = objects_from_query(id_meta_query, id)
        
        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500
        
        schema = self._meta_schema()
        results = []
        for meta in meta_objects:
            relevant_facts_query = f"SELECT * FROM {self._fact_tablename} WHERE {self._fact_to_meta_field_attr} = ?"

            try:
                connection = pyodbc.connect(db_connection_settings)
                cursor = connection.cursor()
                cursor.execute(relevant_facts_query, meta.UUID)
                relevant_facts = cursor.fetchall()

            except pyodbc.Error as odbc_ex:
                connection.close()
                return handle_odbc_exception(odbc_ex), 500
            
            connection.close()
            fact = generate_fact(
                relevant_facts, self._fact_schema)
            result = {**meta, **fact}
            results.append(self._read_schema().dump(result))
        return(results), 200


class FeitenList(Resource):

    def __init__(self, meta_schema, meta_tablename, fact_schema, fact_tablename, fact_to_meta_field, read_schema):
        # Fields that cannot be send for API POST
        self._excluded_meta_post_fields = [
            'ID', 'UUID', 'Modified_By',
            'Modified_Date', 'Created_Date', 
            'Created_By', 'Modified_By'
            ]
        self._excluded_fact_post_fields = [
            'ID', 'UUID', 'Modified_By',
            'Modified_Date', 'Created_Date', 
            'Created_By', 'Begin_Geldigheid', 'Eind_Geldigheid'
            ]

        # Fields that cannot be used for SQL INSERT
        self._excluded_create_fields = ["UUID", "ID"]

        self.all_query = f'SELECT * FROM {meta_tablename}'
        self._meta_tablename = meta_tablename
        self._meta_schema = meta_schema
        self._fact_schema = fact_schema
        self._fact_to_meta_field_attr = fact_schema(
        ).declared_fields[fact_to_meta_field].attribute
        self._fact_to_meta_field = fact_to_meta_field
        self._fact_tablename = fact_tablename
        self._excluded_fact_post_fields.append(fact_to_meta_field)
        self._read_schema = read_schema

    def get(self):
        """
        GET endpoint voor feiten
        """
        all_meta_query = f"SELECT * FROM {self._meta_tablename} WHERE UUID != '00000000-0000-0000-0000-000000000000'"
        
        try:
            meta_objects = objects_from_query(all_meta_query)
        
        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500
        
        schema = self._meta_schema()
        results = []
        for meta in meta_objects:
            relevant_facts_query = f"SELECT * FROM {self._fact_tablename} WHERE {self._fact_to_meta_field_attr} = ?"

            try:
                connection = pyodbc.connect(db_connection_settings)
                cursor = connection.cursor()
                cursor.execute(relevant_facts_query, meta.UUID)
                relevant_facts = cursor.fetchall()

            except pyodbc.Error as odbc_ex:
                connection.close()
                return handle_odbc_exception(odbc_ex), 500
            
            connection.close()
            fact = generate_fact(
                relevant_facts, self._fact_schema)
            result = {**meta, **fact}
            results.append(self._read_schema().dump(result))
        return(results), 200

    def post(self):
        """
        POST endpoint voor feiten
        """
        try:
            meta_schema = self._meta_schema(
                exclude=self._excluded_meta_post_fields,
                unknown=MM.utils.EXCLUDE
            )
            fact_schema = self._fact_schema(
                exclude=self._excluded_fact_post_fields,
                unknown=MM.utils.EXCLUDE
            )
        except ValueError as err:
            return {'message': 'Server fout in endpoint, neeem contact op met de administrator'}, 500

        allowed_fields = generate_allowed_fields(meta_schema, fact_schema, self._excluded_meta_post_fields)
        invalid_fields = [field for field in request.get_json().keys() if (field not in allowed_fields)]

        if invalid_fields:
            return {field: ['Unknown field.'] for field in invalid_fields}, 400

        if request.get_json() is None:
            return {'message': 'Request data empty'}, 400

        try:
            meta_object = meta_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        try:
            fact_object = fact_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        linked_rows = generate_rows(
            fact_schema, fact_object, self._fact_to_meta_field, self._excluded_fact_post_fields)

        meta_object['Created_By'] = get_jwt_identity()['UUID']
        meta_object['Created_Date'] = datetime.datetime.now()
        meta_object['Modified_Date'] = meta_object['Created_Date']
        meta_object['Modified_By'] = meta_object['Created_By']

        try:
            connection = pyodbc.connect(db_connection_settings)
            cursor = connection.cursor()

            meta_field_order, meta_create_query = generate_meta_insert(self._meta_tablename, meta_schema, self._excluded_create_fields)       
            cursor.execute(meta_create_query, *[meta_object[field] for field in meta_field_order])
        
            outputted = cursor.fetchone()
            fact_uuid = outputted[0]
            fact_id = outputted[1]
            
            if linked_rows:
                fact_field_order, fact_create_query = generate_fact_insert(
                    linked_rows, self._fact_tablename, fact_schema, self._fact_to_meta_field, self._excluded_create_fields, self._excluded_fact_post_fields)
                for row in linked_rows:
                    for field in fact_field_order:
                        if field == self._fact_to_meta_field_attr:
                                row[self._fact_to_meta_field_attr] = fact_uuid
                        elif field not in row.keys():
                            row[field] = meta_object[field]  # any field not filled in should be in the meta object
                    cursor.execute(fact_create_query, *[row[field] for field in fact_field_order])
            
            connection.commit()
        
        except pyodbc.Error as odbc_ex:
            connection.close()
            return handle_odbc_exception(odbc_ex), 500
        
        connection.close()
        result = {**meta_object, **fact_object}
        result['UUID'] = fact_uuid
        result['ID'] = fact_id
        return self._read_schema().dump(result), 200
