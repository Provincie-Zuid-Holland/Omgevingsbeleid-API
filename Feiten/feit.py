import marshmallow as MM
import records
import pyodbc
from flask_restful import Resource
from globals import db_connection_string, db_connection_settings

# FEIT:
# - Metadata object
# - Koppelingen object
# Zelfde veld als join

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

class FeitenList(Resource):

    def __init___(self, tableschema, tablename_all, connectionschema):
        self.all_query = f'SELECT * FROM {tablename_all}'
        self._tableschema = tableschema

    def get(self):
        """
        GET endpoint voor feiten
        """
        feiten_objecten = objects_from_query(self.all_query)
        schema = self._tableschema()
        return(schema.dump(feiten_objecten, many=True))