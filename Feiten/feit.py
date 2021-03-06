import marshmallow as MM
from flask_restful import Resource
from flask import request, jsonify
import datetime
from flask_jwt_extended import get_jwt_identity
import pyodbc
from globals import db_connection_string, db_connection_settings, min_datetime, max_datetime
import json
import datetime
# TODO:
# PATCH verwijderd eigenaren op bbs!

def handle_odbc_exception(odbc_ex):
    code = odbc_ex.args[0]
    return {"message": f"Database error [{code}] during handling of request", "detailed": str(odbc_ex)}


class Feiten_Schema(MM.Schema):
    """
    Schema voor de standaard velden van een feit
    """
    ID = MM.fields.Integer(obprops=['excluded_patch', 'excluded_post'])
    UUID = MM.fields.UUID(required=True, obprops=['excluded_patch', 'excluded_post'])
    Begin_Geldigheid = MM.fields.DateTime(format='iso', missing=min_datetime, allow_none=True, obprops=[])
    Eind_Geldigheid = MM.fields.DateTime(format='iso', missing=max_datetime, allow_none=True, obprops=[])
    Created_By = MM.fields.UUID(required=True, obprops=['excluded_patch', 'excluded_post'])
    Created_Date = MM.fields.DateTime(format='iso', required=True, obprops=['excluded_patch', 'excluded_post'])
    Modified_By = MM.fields.UUID(required=True, obprops=['excluded_patch', 'excluded_post'])
    Modified_Date = MM.fields.DateTime(format='iso', required=True, obprops=['excluded_patch', 'excluded_post'])

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

    def none_to_minmax_datetime(self, data):
        if 'Begin_Geldigheid' in data and data['Begin_Geldigheid'] == None:
            data['Begin_Geldigheid'] = min_datetime
        if 'Eind_Geldigheid' in data and data['Eind_Geldigheid'] == None:
            data['Eind_Geldigheid'] = max_datetime
        return data

    @MM.post_load()
    def none_to_minmax_datetime_many(self, data, many, partial):
        if many:
            return list(map(self.none_to_minmax_datetime, data))
        else:
            return self.none_to_minmax_datetime(data)
    
    @classmethod
    def fields_with_props(cls, prop):
        """
        Class method that returns all fields that have `prop`value in their obprops list.
        Returns a list
        """
        return list(map(lambda item: item[0], filter(lambda item: prop in item[1].metadata['obprops'], cls._declared_fields.items())))


    class Meta:
        ordered = True


class Link_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Omschrijving = MM.fields.Str(missing="")
    Titel = MM.fields.Str(missing="")

    class Meta:
        ordered = True


class FactManager:

    def __init__(self, meta_schema, meta_tablename, meta_tablename_actueel, meta_tablename_vigerend, fact_schema, fact_tablename, fact_view, fact_to_meta_field, read_schema, db_connection_settings, ignore_null=True):
        self._ignore_null = ignore_null
        self.db_connection_settings = db_connection_settings
        self._meta_tablename = meta_tablename
        self._meta_tablename_actueel = meta_tablename_actueel
        self._meta_tablename_vigerend = meta_tablename_vigerend
        self._fact_tablename = fact_tablename
        self._fact_view = fact_view
        self._fact_to_meta_field_attr = fact_schema().declared_fields[fact_to_meta_field].attribute or fact_to_meta_field
        self._fact_schema = fact_schema
        self._factschema = read_schema
        # Fields that cannot be used for SQL INSERT
        self._excluded_create_fields = ["UUID", "ID"]
        self._inherited_fields = ['Modified_By', 'Modified_Date', 'Created_Date',
                                  'Created_By', 'Begin_Geldigheid', 'Eind_Geldigheid']

    def row_to_dict(self, row):
        """
        Turns a row from pyodbc into a dictionary
        """
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
                            f'fk_{field}' in fact and f'{field}_Omschrijving' in fact and f'{field}_Titel' in fact)
                    except AssertionError:
                        raise Exception(
                            f"Configuration for field '{field}' invalid, missing 'fk_{field}' or '{field}_Omschrijving' or '{field}_Titel' in database. Found fields: {fact.keys()}")
                    link_object = {
                        'UUID': fact[f'fk_{field}'], 'Omschrijving': fact[f'{field}_Omschrijving'], 'Titel': fact[f'{field}_Titel']}
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
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(self.row_to_dict(row))
        connection.close()
        return results

    def save_fact(self, fact, id=None):
        """
        Saves a schema based fact object to the database.
        """
        schema_fields = self._factschema().declared_fields
        linker_fields = self._factschema.fields_with_props('linker')

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
        return fact

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
            facts_query = f"SELECT * FROM {self._fact_view} WHERE {self._fact_to_meta_field_attr} = ?"

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

        return(self._factschema().dump(meta))

    def retrieve_facts(self, id=None, latest=False, sorted_by=None, vigerend=False):
        """
        Retrieves a list of schema based facts, optionally specify an id to get a lineage.
        """
        if vigerend:
            meta_query = f"SELECT * FROM {self._meta_tablename_vigerend} WHERE ? < Eind_Geldigheid AND ? > Begin_Geldigheid"
        else:
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
            elif vigerend:
                fact_objects = self.facts_from_query(meta_query, datetime.datetime.now(), datetime.datetime.now())
            else:
                fact_objects = self.facts_from_query(meta_query)
        except pyodbc.Error as odbc_ex:
            raise odbc_ex
        if len(fact_objects) == 0:
            return []
        if id and latest:
            fact_object = fact_objects[0]
            return(self._factschema().dump(fact_object))
        return(self._factschema().dump(fact_objects, many=True))


class FeitenLineage(Resource):
    def __init__(self, meta_schema, meta_tablename, meta_tablename_actueel, meta_tablename_vigerend, fact_schema, fact_tablename, fact_view, fact_to_meta_field, read_schema):
        self._factschema = read_schema
        self.manager = FactManager(meta_schema, meta_tablename, meta_tablename_actueel, meta_tablename_vigerend, fact_schema, fact_tablename, fact_view, fact_to_meta_field, read_schema, db_connection_settings)

    def get(self, id):
        """
        Returns a list of versions for a given lineage ID
        """
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
        'Modifies' a given object, by creating a new object and adding it to the lineage list
        """
        request_time = datetime.datetime.now()
        read_schema = self._factschema(
            exclude=self._factschema.fields_with_props('excluded_patch'),
            unknown=MM.utils.RAISE,
            partial=True
        )
        try:
            new_fact = read_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        old_fact = self.manager.retrieve_facts(id, latest=True)
        if not old_fact:
            return {'message': f'Object with ID: \'{id}\' not found'}, 404

        new_fact = self._factschema().dump(new_fact)

        # Combine old fields with new changes
        new_fact = {**old_fact, **new_fact}  

        new_fact['Modified_By'] = get_jwt_identity()['UUID']
        new_fact['Modified_Date'] = MM.utils.isoformat(request_time)
        try:
            new_fact = self._factschema().load(new_fact)
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 500

        try:
            fact = self.manager.save_fact(new_fact, id=id)
            return self._factschema().dump(fact), 200
        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400


def filter_linker(linker, value):
    for field in linker:
        if field['UUID'] == value:
            return True
    return False


def dedup_dictlist(key, dlist):
    """
    Given a list of dictionaries and a key thats in all of those dictionaries, remove all duplicate dictionaries (based on the key)
    """
    keylist = [(d[key], d) for d in dlist]
    keyset = set([d[key] for d in dlist])
    results = []
    for key in keyset:
        for key_, d in keylist:
            if key_ == key:
                results.append(d)
                break
    return results


class FeitenList(Resource):

    def __init__(self, meta_schema, meta_tablename, meta_tablename_actueel, meta_tablename_vigerend, fact_schema, fact_tablename, fact_view, fact_to_meta_field, read_schema):
        self._factschema = read_schema
        self.manager = FactManager(meta_schema, meta_tablename, meta_tablename_actueel, meta_tablename_vigerend, fact_schema, fact_tablename, fact_view, fact_to_meta_field, read_schema, db_connection_settings)

    def get(self):
        """
        GET endpoint voor feiten
        """
        filters = request.args  # TODO: put filtering in DB!
        linker_filters = {}
        normal_filters = {}
        if filters:
            schema_fields = self._factschema().fields
            invalids = [f for f in filters if f not in schema_fields]
            if invalids:
                return {'message': f"Filter(s) '{' '.join(invalids)}' niet geldig voor dit type object. Geldige filters: '{', '.join(schema_fields)}''"}, 403
            linker_filters = {k: v for k, v in filters.items() if k in self._factschema.fields_with_props('linker')}
            normal_filters = {k: v for k, v in filters.items() if k not in linker_filters}
        try:
            if 'Status' in normal_filters and normal_filters['Status'] == 'Vigerend': #TODO: Move to DB!
                unfiltered = self.manager.retrieve_facts(vigerend=True)
            else:
                unfiltered = self.manager.retrieve_facts(latest=True)
            if linker_filters or normal_filters:
                result = []
                for field, value in linker_filters.items():
                    result += list(filter(lambda o: filter_linker(o[field], value), unfiltered))
                for field, value in normal_filters.items():
                    result += list(filter(lambda o: o[field] == value, unfiltered))
                return dedup_dictlist('UUID', result), 200
                # return result, 200
            else:
                return unfiltered, 200

        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500

    def post(self):
        """
        POST endpoint voor feiten
        """
        read_schema = self._factschema(
            exclude=self._factschema.fields_with_props('excluded_post'),
            unknown=MM.utils.RAISE
        )
        try:
            fact = read_schema.load(request.get_json())
            fact['Created_By'] = get_jwt_identity()['UUID']
            fact['Created_Date'] = datetime.datetime.now()
            fact['Modified_Date'] = fact['Created_Date']
            fact['Modified_By'] = fact['Created_By']
            fact['Aanpassing_Op'] = None

        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        try:
            fact = self.manager.save_fact(fact)
            return self._factschema().dump(fact), 200
        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400


class Feit(Resource):

    def __init__(self, meta_schema, meta_tablename, meta_tablename_actueel, meta_tablename_vigerend, fact_schema, fact_tablename, fact_view, fact_to_meta_field, read_schema):
        self.manager = FactManager(meta_schema, meta_tablename, meta_tablename_actueel, meta_tablename_vigerend, fact_schema, fact_tablename, fact_view, fact_to_meta_field, read_schema, db_connection_settings)

    def get(self, uuid):
        try:
            result = self.manager.retrieve_fact(uuid)
            if result is None:
                return {'message': f'Object with UUID: \'{uuid}\' not found'}, 404
            else:
                return result, 200

        except pyodbc.Error as odbc_ex:
            return handle_odbc_exception(odbc_ex), 500
