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

class Doel_Schema(MM.Schema):
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

class Doel(Resource):
    """Deze resource vertegenwoordigd de Doelen van de provincie"""
    def get(self, doel_uuid=None):
        if doel_uuid:
            doel = single_object_by_uuid('Doel', doel_op_uuid, uuid=doel_uuid)
            
            if not doel:
                return {'message': f"Doel met UUID {doel_uuid} is niet gevonden"}, 400
            
            schema = Doel_Schema()
            return(schema.dump(doel))
        else:    
            doelen = objects_from_query('Doel', alle_doelen)

            schema = Doel_Schema()
            return(schema.dump(doelen, many=True))

    def post(self, doel_uuid=None):
        if doel_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
        schema = Doel_Schema(
            exclude = ('UUID', 'Modified_By', 'Modified_Date'),
            unknown = MM.utils.RAISE)
        try:
            doel = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(doel_aanmaken,
        doel['Titel'],
        doel['Omschrijving'],
        doel['Weblink'],
        doel['Begin_Geldigheid'],
        doel['Eind_Geldigheid'],
        doel['Created_By'],
        doel['Created_Date'],
        doel['Created_By'],
        doel['Created_Date'])
        new_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}
    
    def patch(self, doel_uuid=None):
        if not doel_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
        patch_schema = Doel_Schema(
            partial=('Titel', 'Omschrijving', 'Weblink', 'Begin_Geldigheid', 'Eind_Geldigheid'),
            exclude = ('UUID', 'Created_By', 'Created_Date'),
            unknown=MM.utils.RAISE
            )
        try:
            doel_aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
            
        oud_doel = single_object_by_uuid('Doelen', doel_op_uuid, uuid=doel_uuid)
        
        if not oud_doel:
            return {'message': f"Doel met UUID {doel_uuid} is niet gevonden"}, 400
            
        doel = {**oud_doel, **doel_aanpassingen}
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(
        doel_aanpassen,
        doel['ID'],
        doel['Titel'],
        doel['Omschrijving'],
        doel['Weblink'],
        doel['Begin_Geldigheid'],
        doel['Eind_Geldigheid'],
        doel['Created_By'],
        doel['Created_Date'],
        doel['Modified_By'],
        doel['Modified_Date'])
        new_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}


