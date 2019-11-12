import marshmallow as MM
from flask_restful import Resource
from flask import request, jsonify
import datetime
from flask_jwt_extended import get_jwt_identity
import pyodbc
from globals import db_connection_string, db_connection_settings
import json


def handle_odbc_exception(odbc_ex):
    code = odbc_ex.args[0]
    return {"message": f"Database error [{code}] during handling of request", "detailed": str(odbc_ex)}


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


class FactManager:

    def __init__(self, meta_schema, meta_tablename, meta_tablename_actueel, fact_schema, fact_tablename, fact_to_meta_field, read_schema, db_connection_settings, ignore_null=True):
        self._ignore_null = ignore_null
        self.db_connection_settings = db_connection_settings
        self._meta_tablename = meta_tablename
        self._meta_tablename_actueel = meta_tablename_actueel
        self._fact_tablename = fact_tablename
        self._fact_to_meta_field_attr = fact_schema().declared_fields[fact_to_meta_field].attribute or fact_to_meta_field
        self._fact_schema = fact_schema
        self._read_schema = read_schema
        # Fields that cannot be used for SQL INSERT
        self._excluded_create_fields = ["UUID", "ID"]
        self._inherited_fields = ['Modified_By', 'Modified_Date', 'Created_Date',
                                  'Created_By', 'Begin_Geldigheid', 'Eind_Geldigheid']

    def row_to_dict(self, row):
        return dict(zip([t[0] for t in row.cursor_description], row))

    def generate_fact(self, facts):
        """
        Turns a set of flat rows into a schema with nested relationships
        """
        schema = self._fact_schema()
        result = {}
        for fact in facts:
            fact = self.row_to_dict(fact)
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
        return(result)

    def objects_from_query(self, query, *args):
        """
        Retrieve all object from a query as list of dicts
        """
        connection = pyodbc.connect(self.db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(query, *args)
        headers = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(dict(zip(headers, row)))
        connection.close()
        return results

    def save_fact(self, fact, id=None):
        """
        Saves a schema based fact object to the database.
        """
        schema_fields = self._read_schema().declared_fields
        linker_fields = []
        for name, field in schema_fields.items():
            if 'linker' in field.metadata:
                if field.metadata['linker']:
                    linker_fields.append(name)

        linker_fields_max_len = max(map(lambda fieldname: len(fact[fieldname]), linker_fields))
        linked_rows = []
        for i in range(linker_fields_max_len):
            linked_rows.append({})
            for field in linker_fields:
                try:
                    linked = fact[field][i]
                except IndexError:
                    linked = {"UUID": "00000000-0000-0000-0000-000000000000",
                              "Omschrijving": None}
                linked_rows[i][f'fk_{field}'] = linked['UUID']
                linked_rows[i][f'{field}_Omschrijving'] = linked['Omschrijving']

        try:
            connection = pyodbc.connect(db_connection_settings)
            cursor = connection.cursor()

            # meta create
            meta_create_values = ""
            meta_create_fields = ""
            meta_field_order = []
            for field in schema_fields:
                if field not in linker_fields and field not in self._excluded_create_fields:
                    if schema_fields[field].attribute:
                        meta_create_fields += f"[{field.attribute}], "
                    else:
                        meta_create_fields += f"[{field}], "
                    meta_create_values += "?, "
                    meta_field_order.append(field)
            if id:
                meta_create_fields += f"[ID], "
                meta_create_values += "?, "
                meta_field_order.append("ID")
                fact["ID"] = id
            meta_create_fields = meta_create_fields[:-2]
            meta_create_values = meta_create_values[:-2]

            meta_create_query = f'''INSERT INTO [{self._meta_tablename}] ({meta_create_fields}) OUTPUT inserted.UUID, inserted.ID VALUES ({meta_create_values})'''

            cursor.execute(meta_create_query, *[fact[field] for field in meta_field_order])

            outputted = cursor.fetchone()
            fact_uuid = outputted[0]
            fact_id = outputted[1]

            if linked_rows:
                for row in linked_rows:
                    row[self._fact_to_meta_field_attr] = fact_uuid
                    for field in self._inherited_fields:
                        row[field] = fact[field]

                fact_create_fields = ""
                fact_create_values = ""
                fact_field_order = []
                all_fields = list(linked_rows[0].keys())
                for field in all_fields:
                    fact_create_fields += f"[{field}], "
                    fact_create_values += "?, "
                    fact_field_order.append(field)
                fact_create_fields = fact_create_fields[:-2]
                fact_create_values = fact_create_values[:-2]
                fact_create_query = f'''INSERT INTO [{self._fact_tablename}] ({fact_create_fields}) VALUES ({fact_create_values})'''

                for row in linked_rows:
                    cursor.execute(fact_create_query, *[row[field] for field in fact_field_order])
            connection.commit()

        except pyodbc.Error as odbc_ex:
            raise odbc_ex
        finally:
            connection.close()

        fact['UUID'] = fact_uuid
        fact['ID'] = fact_id
        return self._read_schema().dump(fact)

    def facts_from_query(self, query, *args):
        """
        Executes a query on meta objects and returns complete facts
        """
        try:
            meta_objects = self.objects_from_query(query, *args)
        except pyodbc.Error as odbc_ex:
            raise odbc_ex
        results = []
        for meta in meta_objects:
            facts_query = f"SELECT * FROM {self._fact_tablename} WHERE {self._fact_to_meta_field_attr} = ?"

            try:
                connection = pyodbc.connect(self.db_connection_settings)
                cursor = connection.cursor()
                cursor.execute(facts_query, meta['UUID'])
                relevant_facts = cursor.fetchall()

            except pyodbc.Error as odbc_ex:
                raise odbc_ex

            finally:
                connection.close()

            fact = self.generate_fact(
                
                relevant_facts)
            result = {**meta, **fact}
            results.append(result)
        return results

    def retrieve_fact(self, uuid):
        """
        Retrieves a schema based fact object from the database.
        """
        meta_query = f"SELECT * FROM {self._meta_tablename} WHERE UUID = ?"
        if self._ignore_null:
            meta_query += " AND UUID != '00000000-0000-0000-0000-000000000000'"
        try:
            fact_objects = self.facts_from_query(meta_query, uuid)
        except pyodbc.Error as odbc_ex:
            raise odbc_ex

        if len(fact_objects) == 0:
            return None

        assert(len(fact_objects) == 1), 'Multiple results where singular object was expected (duplicate UUID)'
        meta = fact_objects[0]

        return(self._read_schema().dump(meta))

    def retrieve_facts(self, id=None, latest=False, sorted_by=None):
        """
        Retrieves a list of schema based facts, optionally specify an id to get a lineage.
        """
        if id and latest:
            meta_query = f"SELECT * FROM {self._meta_tablename_actueel} WHERE ID = ?"
        elif id:
            meta_query = f"SELECT * FROM {self._meta_tablename} WHERE ID = ?"
            if self._ignore_null:
                meta_query += " AND UUID != '00000000-0000-0000-0000-000000000000'"
        elif latest:
            meta_query = f"SELECT * FROM {self._meta_tablename_actueel}"
            if self._ignore_null:
                meta_query += " WHERE UUID != '00000000-0000-0000-0000-000000000000'"
        else:
            meta_query = f"SELECT * FROM {self._meta_tablename}"
            if self._ignore_null:
                meta_query += " WHERE UUID != '00000000-0000-0000-0000-000000000000'"
        if sorted_by:
            meta_query += f"ORDER BY {sorted_by} DESC"

        try:
            if id:
                fact_objects = self.facts_from_query(meta_query, id)
            else:
                fact_objects = self.facts_from_query(meta_query)
        except pyodbc.Error as odbc_ex:
            raise odbc_ex
        if len(fact_objects) == 0:
            return []
        if id and latest:
            fact_object = fact_objects[0]
            return(self._read_schema().dump(fact_object))
        return(self._read_schema().dump(fact_objects, many=True))


class FeitenLineage(Resource):
    def __init__(self, meta_schema, meta_tablename, meta_tablename_actueel, fact_schema, fact_tablename, fact_to_meta_field, read_schema):
        # Fields that cannot be send for API POST
        self._excluded_meta_patch_fields = [
            'ID', 'UUID', 'Modified_By',
            'Modified_Date', 'Created_Date',
            'Created_By'
        ]
        self._excluded_fact_patch_fields = [
            'ID', 'UUID', 'Modified_By',
            'Modified_Date', 'Created_Date',
            'Created_By', 'Begin_Geldigheid', 'Eind_Geldigheid'
        ]

        # Fields that cannot be used for SQL INSERT
        self._excluded_create_fields = ["UUID", "ID"]

        self._meta_tablename = meta_tablename
        self._meta_schema = meta_schema
        self._fact_schema = fact_schema
        self._fact_to_meta_field_attr = fact_schema(
        ).declared_fields[fact_to_meta_field].attribute
        self._fact_to_meta_field = fact_to_meta_field
        self._fact_tablename = fact_tablename
        self._read_schema = read_schema
        self.manager = FactManager(meta_schema, meta_tablename, meta_tablename_actueel, fact_schema, fact_tablename, fact_to_meta_field, read_schema, db_connection_settings)

    def get(self, id):
        try:
            result = self.manager.retrieve_facts(id=id, sorted_by='Modified_Date')
            if len(result) == 0:
                return {'message': f'Object with ID: \'{id}\' not found'}, 404
            else:
                return result, 200

        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500

    def patch(self, id):
        """
        PATCH endpoint voor feiten
        """
        request_time = datetime.datetime.now()
        read_schema = self._read_schema(
            exclude=self._excluded_meta_patch_fields,
            unknown=MM.utils.RAISE,
            partial=True
        )
        try:
            new_fact = read_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        old_fact = self.manager.retrieve_facts(id, latest=True)
        new_fact = self._read_schema().dump(new_fact)
        
        new_fact = {**old_fact, **new_fact}  # Dict merging
        new_fact['Modified_By'] = get_jwt_identity()['UUID']
        new_fact['Modified_Date'] = MM.utils.isoformat(request_time)
        try:
            new_fact = self._read_schema().load(new_fact)
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 500

        try:
            return self.manager.save_fact(new_fact, id=id), 200
        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500


class FeitenList(Resource):

    def __init__(self, meta_schema, meta_tablename, meta_tablename_actueel, fact_schema, fact_tablename, fact_to_meta_field, read_schema):
        # Fields that cannot be send for API POST
        self._excluded_meta_post_fields = [
            'ID', 'UUID', 'Modified_By',
            'Modified_Date', 'Created_Date',
            'Created_By'
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
        self.manager = FactManager(meta_schema, meta_tablename, meta_tablename_actueel, fact_schema, fact_tablename, fact_to_meta_field, read_schema, db_connection_settings)

    def get(self):
        """
        GET endpoint voor feiten
        """
        try:
            result = self.manager.retrieve_facts(latest=True)
            return result, 200

        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500

    def post(self):
        """
        POST endpoint voor feiten
        """
        read_schema = self._read_schema(
            exclude=self._excluded_meta_post_fields,
            unknown=MM.utils.RAISE
        )
        try:
            fact = read_schema.load(request.get_json())
            fact['Created_By'] = get_jwt_identity()['UUID']
            fact['Created_Date'] = datetime.datetime.now()
            fact['Modified_Date'] = fact['Created_Date']
            fact['Modified_By'] = fact['Created_By']

        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        try:
            return self.manager.save_fact(fact), 200
        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500


class Feit(Resource):

    def __init__(self, meta_schema, meta_tablename, meta_tablename_actueel, fact_schema, fact_tablename, fact_to_meta_field, read_schema):
        self.manager = FactManager(meta_schema, meta_tablename, meta_tablename_actueel, fact_schema, fact_tablename, fact_to_meta_field, read_schema, db_connection_settings)

    def get(self, uuid):
        try:
            result = self.manager.retrieve_fact(uuid)
            if result is None:
                return {'message': f'Object with UUID: \'{uuid}\' not found'}, 404
            else:
                return result, 200

        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500
