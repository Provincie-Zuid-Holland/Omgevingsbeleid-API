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

class Geothema_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Titel = MM.fields.Str(required=True)
    Omschrijving = MM.fields.Str(missing=None)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.Str(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.Str(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)

    class Meta:
        ordered = True
    


class Geothema(Resource):
    """Deze resource vertegenwoordigd de Ambities van de provincie"""
    # @swag_from('geothema.yml')
    def get(self, geothema_uuid=None):
        if geothema_uuid:
            geothema = single_object_by_uuid('Geothemas', geothema_op_uuid, uuid=geothema_uuid)        
            
            if not geothema:
                return {'message': f"Geothema met UUID {geothema_uuid} is niet gevonden"}, 400
            
            schema = Geothema_Schema()
            return(schema.dump(geothema))
        else:    
            geothemas = objects_from_query('Geothemas', alle_geothemas)
            
            schema = Geothema_Schema()
            return(schema.dump(geothemas, many=True))


