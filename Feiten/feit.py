import marshmallow as MM
import records
import pyodbc
from flask_restful import Resource
from flask import request, jsonify
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
                    assert(f'fk_{field}' in fact and f'{field}_Omschrijving' in fact)
                except AssertionError:
                    raise Exception(f"Configuration for field '{field}' invalid, missing 'fk_{field}' or '{field}_Omschrijving' in database")
                link_object = {'UUID': fact[f'fk_{field}'], 'Omschrijving': fact[f'{field}_Omschrijving']}
                if link_object['UUID'] or link_object['Omschrijving']:
                    if field in result:
                        result[field].append(link_object)
                    else:
                        result[field] = [link_object]
    return(schema.dump(result))


class FeitenList(Resource):

    _excluded_post_fields = ['ID', 'UUID', 'Modified_By', 'Modified_Date', 'Created_Date', 'Created_By', 'Modified_By' ]

    def __init__(self, meta_schema, meta_tablename, fact_schema, fact_tablename, fact_to_meta_field):
        self.all_query = f'SELECT * FROM {meta_tablename}'
        self._meta_schema = meta_schema
        self._fact_schema = fact_schema
        self._fact_to_meta_field = fact_to_meta_field
        self._fact_tablename = fact_tablename

    def get(self):
        """
        GET endpoint voor feiten
        """
        fact_objects = objects_from_query(self.all_query)
        schema = self._meta_schema()
        results = []
        for fact in fact_objects:
            meta = generate_fact(fact.UUID, self._fact_tablename, self._fact_to_meta_field, self._fact_schema)
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
                exclude = self._excluded_post_fields
            )
            fact_schema = self._fact_schema()
        except ValueError:
            return {'message': 'Server fout in endpoint, neeem contact op met de administrator'}, 500
        
        if request.get_json() == None:
            return {'message': 'Request data empty'}, 400

        try:
            meta_object = meta_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        return jsonify(meta_object)
