from flask_restful import Resource, Api, fields, marshal, reqparse, inputs, abort
import records
import pyodbc
from flasgger import swag_from
import marshmallow as MM 
from flask import request

from queries import *
from helpers import single_object_by_uuid, objects_from_query, related_objects_from_query, validate_UUID
from globals import db_connection_string, db_connection_settings
from uuid import UUID


class Werkingsgebied_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    OBJECTID = MM.fields.Integer(required=True)
    Werkingsgebied = MM.fields.Str(required=True)
    Onderverdeling = MM.fields.Str(missing=None)
    PRIMA = MM.fields.Integer()
    FID = MM.fields.Integer()
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.Str(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.Str(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)

    class Meta:
        ordered = True
    


class Werkingsgebied(Resource):
    """Deze resource vertegenwoordigd de Ambities van de provincie"""
    # @swag_from('werkingsgebied.yml')
    def get(self, werkingsgebied_uuid=None):
        if werkingsgebied_uuid:
            werkingsgebied = single_object_by_uuid('Werkingsgebieden', werkingsgebied_op_uuid, uuid=werkingsgebied_uuid)        
            
            if not werkingsgebied:
                return {'message': f"Werkingsgebied met UUID {werkingsgebied_uuid} is niet gevonden"}, 400
            
            schema = Werkingsgebied_Schema()
            return(schema.dump(werkingsgebied))
        else:    
            werkingsgebieden = objects_from_query('Werkingsgebieden', alle_werkingsgebieden)
            
            schema = Werkingsgebied_Schema()
            return(schema.dump(werkingsgebieden, many=True))


