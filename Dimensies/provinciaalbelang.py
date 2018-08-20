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

class Provinciaalbelang_Schema(MM.Schema):
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

class ProvinciaalBelang(Resource):
    """Deze resource vertegenwoordigd de Provinciaalbelangen van de provincie"""
    def get(self, provinciaalbelang_uuid=None):
        if provinciaalbelang_uuid:
            provinciaalbelang = single_object_by_uuid('Provinciaalbelang', provinciaalbelang_op_uuid, uuid=provinciaalbelang_uuid)
            
            if not provinciaalbelang:
                return {'message': f"Provinciaalbelang met UUID {provinciaalbelang_uuid} is niet gevonden"}, 400
            
            schema = Provinciaalbelang_Schema()
            return(schema.dump(provinciaalbelang))
        else:    
            provinciaalbelangen = objects_from_query('Provinciaalbelang', alle_provincialebelangen)

            schema = Provinciaalbelang_Schema()
            return(schema.dump(provinciaalbelangen, many=True))

    def post(self, provinciaalbelang_uuid=None):
        if provinciaalbelang_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
        schema = Provinciaalbelang_Schema(
            exclude = ('UUID', 'Modified_By', 'Modified_Date'),
            unknown = MM.utils.RAISE)
        try:
            provinciaalbelang = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(provinciaalbelang_aanmaken,
        provinciaalbelang['Titel'],
        provinciaalbelang['Omschrijving'],
        provinciaalbelang['Weblink'],
        provinciaalbelang['Begin_Geldigheid'],
        provinciaalbelang['Eind_Geldigheid'],
        provinciaalbelang['Created_By'],
        provinciaalbelang['Created_Date'],
        provinciaalbelang['Created_By'],
        provinciaalbelang['Created_Date'])
        new_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}
    
    def patch(self, provinciaalbelang_uuid=None):
        if not provinciaalbelang_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
        patch_schema = Provinciaalbelang_Schema(
            partial=('Titel', 'Omschrijving', 'Weblink', 'Begin_Geldigheid', 'Eind_Geldigheid'),
            exclude = ('UUID', 'Created_By', 'Created_Date'),
            unknown=MM.utils.RAISE
            )
        try:
            provinciaalbelang_aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
            
        oud_provinciaalbelang = single_object_by_uuid('Provinciaalbelangen', provinciaalbelang_op_uuid, uuid=provinciaalbelang_uuid)
        
        if not oud_provinciaalbelang:
            return {'message': f"Provinciaalbelang met UUID {provinciaalbelang_uuid} is niet gevonden"}, 400
            
        provinciaalbelang = {**oud_provinciaalbelang, **provinciaalbelang_aanpassingen}
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(
        provinciaalbelang_aanpassen,
        provinciaalbelang['ID'],
        provinciaalbelang['Titel'],
        provinciaalbelang['Omschrijving'],
        provinciaalbelang['Weblink'],
        provinciaalbelang['Begin_Geldigheid'],
        provinciaalbelang['Eind_Geldigheid'],
        provinciaalbelang['Created_By'],
        provinciaalbelang['Created_Date'],
        provinciaalbelang['Modified_By'],
        provinciaalbelang['Modified_Date'])
        new_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}


