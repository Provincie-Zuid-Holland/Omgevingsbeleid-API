import marshmallow as MM
import records
import pyodbc
from flask_restful import Resource
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

def generate_fact(meta_uuid, fact_tablename, fact_to_meta_field):
    relevant_facts_query = f'SELECT * FROM {fact_tablename} WHERE :ftmf = :muuid'
    db = records.Database(db_connection_string)
    relevant_facts = db.query(relevant_facts_query, ftmf=fact_to_meta_field, muuid=meta_uuid)
    # TODO: THIS DOES NOT RETURN ANY RESULT (IT SHOULD)
    print(meta_uuid)
    for fact in relevant_facts:
        print(fact)
    print("done")
    # print(relevant_facts[0])
    # print(list(relevant_facts))

class FeitenList(Resource):

    def __init__(self, meta_schema, meta_tablename, fact_schema, fact_tablename, fact_to_meta_field):
        self.all_query = f'SELECT * FROM {meta_tablename}'
        self._meta_schema = meta_schema

    def get(self):
        """
        GET endpoint voor feiten
        """
        feiten_objecten = objects_from_query(self.all_query)
        generate_fact(feiten_objecten[1].UUID, 'Omgevingsbeleid', 'fk_Beleidsbeslissingen')
        schema = self._meta_schema()
        raise
        return(schema.dump(feiten_objecten, many=True))