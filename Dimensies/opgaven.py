from flask_restful import Resource, Api, fields, marshal, reqparse, inputs, abort
import records
import pyodbc
from flasgger import swag_from
import marshmallow as MM 
from flask import request
import re

from queries import *
from helpers import *
from globals import db_connection_string, db_connection_settings
from uuid import UUID
    
class Opgaven_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Titel = MM.fields.Str(required=True)
    Omschrijving = MM.fields.Str(missing=None)
    Weblink = MM.fields.Str(missing=None)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.Str(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.Str(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)

    class Meta:
        ordered = True
        

class Opgave(Resource):
    """Deze resource vertegenwoordigd de Beleidsregels van de provincie"""
    # @swag_from('provinciaalbelang.yml')
    def get(self, opgave_uuid=None):
        if opgave_uuid:
            opgave = single_object_by_uuid('Opgave', opgave_op_uuid, uuid=opgave_uuid)
            
            if not opgave:
                return {'message': f"Opgave met UUID {opgave_uuid} is niet gevonden"}, 400
            
            schema = Opgaven_Schema()
            return(schema.dump(opgave))
        else:    
            opgaven = objects_from_query('Opgave', alle_opgaven)
      
            schema = Opgaven_Schema()
            return(schema.dump(opgaven, many=True))

    def post(self, opgave_uuid=None):
        if opgave_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
        
        schema = Opgaven_Schema(
            exclude = ('UUID','Modified_By', 'Modified_Date'),
            unknown=MM.utils.RAISE)
        try:
            opgave = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(opgave_aanmaken,
        opgave['Titel'],
        opgave['Omschrijving'],
        opgave['Weblink'],
        opgave['Begin_Geldigheid'],
        opgave['Eind_Geldigheid'],
        opgave['Created_By'],
        opgave['Created_Date'],
        opgave['Created_By'],
        opgave['Created_Date'])
        opgave_uuid = cursor.fetchone()[0]

        connection.commit()
        return {"Resultaat_UUID": f"{opgave_uuid}"}

    def patch(self, opgave_uuid=None):
        if not opgave_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
        patch_schema = Opgaven_Schema(
            partial=('Titel', 'Omschrijving', 'Weblink', 'Begin_Geldigheid', 'Eind_Geldigheid'),
            exclude = ('UUID', 'Created_By', 'Created_Date')
            )
        try:
            opgave_aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        
        oude_opgave = single_object_by_uuid('Opgaven', opgave_op_uuid, uuid=opgave_uuid)
        
        if not oude_opgave:
            return {'message': f'Opgave met UUID {opgave_uuid} is niet gevonden'}, 400
        
        
        opgave = {**oude_opgave, **opgave_aanpassingen}
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(opgave_aanpassen,
        opgave['ID'],
        opgave['Titel'],
        opgave['Omschrijving'],
        opgave['Weblink'],
        opgave['Begin_Geldigheid'],
        opgave['Eind_Geldigheid'],
        opgave['Created_By'],
        opgave['Created_Date'],
        opgave['Modified_By'],
        opgave['Modified_Date'])
        opgave_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{opgave_uuid}"}
        

