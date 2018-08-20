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

class Thema_Schema(MM.Schema):
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

class Thema(Resource):
    """Deze resource vertegenwoordigd de Themas van de provincie"""
    def get(self, thema_uuid=None):
        if thema_uuid:
            thema = single_object_by_uuid('Thema', thema_op_uuid, uuid=thema_uuid)
            
            if not thema:
                return {'message': f"Thema met UUID {thema_uuid} is niet gevonden"}, 400
            
            schema = Thema_Schema()
            return(schema.dump(thema))
        else:    
            themas = objects_from_query('Thema', alle_themas)

            schema = Thema_Schema()
            return(schema.dump(themas, many=True))

    def post(self, thema_uuid=None):
        if thema_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
        schema = Thema_Schema(
            exclude = ('UUID', 'Modified_By', 'Modified_Date'),
            unknown = MM.utils.RAISE)
        try:
            thema = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(thema_aanmaken,
        thema['Titel'],
        thema['Omschrijving'],
        thema['Begin_Geldigheid'],
        thema['Eind_Geldigheid'],
        thema['Created_By'],
        thema['Created_Date'],
        thema['Created_By'],
        thema['Created_Date'])
        new_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}
    
    def patch(self, thema_uuid=None):
        if not thema_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
        patch_schema = Thema_Schema(
            partial=('Titel', 'Omschrijving', 'Weblink', 'Begin_Geldigheid', 'Eind_Geldigheid'),
            exclude = ('UUID', 'Created_By', 'Created_Date'),
            unknown=MM.utils.RAISE
            )
        try:
            thema_aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
            
        oud_thema = single_object_by_uuid('Themas', thema_op_uuid, uuid=thema_uuid)
        
        if not oud_thema:
            return {'message': f"Thema met UUID {thema_uuid} is niet gevonden"}, 400
            
        thema = {**oud_thema, **thema_aanpassingen}
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(
        thema_aanpassen,
        thema['ID'],
        thema['Titel'],
        thema['Omschrijving'],
        thema['Begin_Geldigheid'],
        thema['Eind_Geldigheid'],
        thema['Created_By'],
        thema['Created_Date'],
        thema['Modified_By'],
        thema['Modified_Date'])
        new_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}


