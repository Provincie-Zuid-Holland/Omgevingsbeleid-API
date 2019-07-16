import marshmallow as MM
import records
import pyodbc
from flask_restful import Resource
from flask import request, jsonify
import datetime
from flask_jwt_extended import get_jwt_identity
import pyodbc
from globals import db_connection_string, db_connection_settings

# FEIT:
# - Metadata object
# - Koppelingen object
# - Definieer veld als join


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


def generate_fact(meta_uuid, fact_tablename, fact_to_meta_field, fact_schema):
    """
    Turns a set of flat rows into a schema with nested relationships
    """
    relevant_facts_query = f"SELECT * FROM {fact_tablename} WHERE {fact_to_meta_field} = :muuid"
    db = records.Database(db_connection_string)
    relevant_facts = db.query(relevant_facts_query, muuid=meta_uuid)
    schema = fact_schema()
    result = {}
    for fact in relevant_facts:
        fact = fact.as_dict()
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


class FeitenList(Resource):

    # Fields that cannot be send for API POST
    _excluded_meta_post_fields = ['ID', 'UUID', 'Modified_By',
                                  'Modified_Date', 'Created_Date', 'Created_By', 'Modified_By']
    _excluded_fact_post_fields = ['ID', 'UUID', 'Modified_By',
                                  'Modified_Date', 'Created_Date', 'Created_By', 'Begin_Geldigheid', 'Eind_Geldigheid']

    # Fields that cannot be used for SQL INSERT
    _excluded_create_fields = ["UUID", "ID"]

    def __init__(self, meta_schema, meta_tablename, fact_schema, fact_tablename, fact_to_meta_field):
        self.all_query = f'SELECT * FROM {meta_tablename}'
        self._meta_tablename = meta_tablename
        self._meta_schema = meta_schema
        self._fact_schema = fact_schema
        self._fact_to_meta_field_attr = fact_schema(
        ).declared_fields[fact_to_meta_field].attribute
        self._fact_to_meta_field = fact_to_meta_field
        self._fact_tablename = fact_tablename
        self._excluded_fact_post_fields.append(fact_to_meta_field)

    def get(self):
        """
        GET endpoint voor feiten
        """
        fact_objects = objects_from_query(self.all_query)
        schema = self._meta_schema()
        results = []
        for fact in fact_objects:
            meta = generate_fact(
                fact.UUID, self._fact_tablename, self._fact_to_meta_field_attr, self._fact_schema)
            fact = schema.dump(fact)
            result = {**fact, **meta}
            results.append(result)
        return(results)

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

        possible_fields = list(
            {**meta_schema.declared_fields, **fact_schema.declared_fields}.keys())
        excluded_fields = self._excluded_meta_post_fields
        allowed_fields = [
            field for field in possible_fields if field not in excluded_fields]
        invalid_fields = [field for field in request.get_json(
        ).keys() if (field not in allowed_fields)]

        if invalid_fields:
            return {field: ['Unknown field.'] for field in invalid_fields}, 400

        # return jsonify(allowed_fields)
        if request.get_json() == None:
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


        # generate an INSERT INTO query for Meta object
        meta_create_fields = ""
        meta_create_values = ""
        meta_field_order = []
        for field in meta_schema.declared_fields:
            if field not in self._excluded_create_fields:
                if meta_schema.declared_fields[field].attribute:
                    meta_create_fields += f"[{field.attribute}], "
                else:
                    meta_create_fields += f"[{field}], "
                meta_create_values += "?, "
                meta_field_order.append(field)
        meta_create_fields = meta_create_fields[:-2]
        meta_create_values = meta_create_values[:-2]
        
        # generate an INSERT INTO query for Fact objects
        if linked_rows:
            fact_create_fields = ""
            fact_create_values = ""
            all_fields = (list(linked_rows[0].keys()) + self._excluded_fact_post_fields) 
            all_create_fields = [field for field in all_fields if field not in self._excluded_create_fields]
            if self._fact_to_meta_field_attr:
                all_create_fields.remove(self._fact_to_meta_field)
                all_create_fields.append(self._fact_to_meta_field_attr)
            for field in all_create_fields:
                fact_create_fields += f"[{field}], "
                fact_create_values += "?, "
            fact_create_fields = fact_create_fields[:-2]
            fact_create_values = fact_create_values[:-2]

        meta_create_query = f'''INSERT INTO [dbo].[{self._meta_tablename}] ({meta_create_fields}) OUTPUT inserted.UUID, inserted.ID VALUES ({meta_create_values})'''
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        
        # TODO: CATCH EM ALL
        cursor.execute(meta_create_query, *[meta_object[field] for field in meta_field_order])
        
        outputted = cursor.fetchone()
        fact_uuid = outputted[0]
        fact_id = outputted[1]
        
        # TODO: CATCH EM ALL
        row_create_query = f'''INSERT INTO [dbo].[{self._fact_tablename}] ({fact_create_fields}) VALUES ({fact_create_values})'''
        for row in linked_rows:
            for field in all_create_fields:
                if field == self._fact_to_meta_field or field == self._fact_to_meta_field_attr:
                    if self._fact_to_meta_field_attr:
                        row[self._fact_to_meta_field_attr] = fact_uuid
                    else:
                        row[field] = fact_uuid
                elif field not in row.keys():
                    row[field] = meta_object[field] # any field not filled in should be in the meta object
            # print(row)
            print(row_create_query)
            cursor.execute(row_create_query, *[row[field] for field in all_create_fields])

        connection.commit()
        connection.close()
        # TODO: Return proper object
        return (fact_uuid + " : " + str(fact_id))
        # return jsonify({**meta_object, **fact_object})
