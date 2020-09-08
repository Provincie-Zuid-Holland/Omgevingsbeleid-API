from flask_restful import Resource, Api, fields, marshal, reqparse, inputs, abort
import pyodbc
import marshmallow as MM 
from flask import request

from globals import db_connection_settings, null_uuid
from uuid import UUID


class Werkingsgebied_Schema(MM.Schema):
    ID = MM.fields.Int(required=True)
    UUID = MM.fields.UUID(required=True)
    Werkingsgebied = MM.fields.Str(required=True, search_field="text")
    symbol = MM.fields.Str(missing=None)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.Str(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.Str(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)

    class Meta:
        ordered = True
    

class Werkingsgebied(Resource):
    def get(self, werkingsgebied_uuid=None):
        fields = Werkingsgebied_Schema().fields.keys()
        with pyodbc.connect(db_connection_settings) as cnx:
            cur = cnx.cursor()
            if werkingsgebied_uuid:
                werkingsgebieden = list(cur.execute(
                    f'SELECT {", ".join(fields)} FROM Werkingsgebieden WHERE UUID = ?', werkingsgebied_uuid))

                if not werkingsgebieden:
                    return {'message': f"Werkingsgebied met UUID {werkingsgebied_uuid} is niet gevonden"}, 400

                schema = Werkingsgebied_Schema()
                return(schema.dump(werkingsgebieden[0]))
            else:
                werkingsgebieden = cur.execute(
                    f"SELECT {', '.join(fields)} FROM Werkingsgebieden WHERE UUID != '{null_uuid}'")
                schema = Werkingsgebied_Schema()
                return(schema.dump(werkingsgebieden, many=True))