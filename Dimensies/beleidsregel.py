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


class BeleidsRegel_Schema(MM.Schema):
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
        

class BeleidsRegel(Resource):
    """Deze resource vertegenwoordigd de Beleidsregels van de provincie"""
    def get(self, beleidsregel_uuid=None):
        if beleidsregel_uuid:           
            beleidsregel = single_object_by_uuid('BeleidsRegel', beleidsregel_op_uuid, uuid=beleidsregel_uuid)
            
            if not beleidsregel:
                return {'message': f"BeleidsRegel met UUID {beleidsregel_uuid} is niet gevonden"}, 400
            
            schema = BeleidsRegel_Schema()
            return schema.dump(beleidsregel)
        else:    
            beleidsregels = objects_from_query('BeleidsRegel', alle_beleidsregels)

            schema = BeleidsRegel_Schema()
            return schema.dump(beleidsregels, many=True)

    def post(self, beleidsregel_uuid=None):
        if beleidsregel_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
        
        schema = BeleidsRegel_Schema(
            exclude = ('UUID','Modified_By', 'Modified_Date'),
            unknown=MM.utils.RAISE)
        try:
            beleidsregel = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

            
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(beleidsregel_aanmaken,
        beleidsregel['Titel'],
        beleidsregel['Omschrijving'],
        beleidsregel['Weblink'],
        beleidsregel['Begin_Geldigheid'],
        beleidsregel['Eind_Geldigheid'],
        beleidsregel['Created_By'],
        beleidsregel['Created_Date'],
        beleidsregel['Created_By'],
        beleidsregel['Created_Date'])
        new_uuid = cursor.fetchone()[0]

        connection.commit()
        
        return {"Resultaat_UUID": f"{new_uuid}"}
    
    def patch(self, beleidsregel_uuid=None):
        if not beleidsregel_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
        patch_schema = BeleidsRegel_Schema(
            partial=('Titel', 'Omschrijving', 'Weblink', 'Begin_Geldigheid', 'Eind_Geldigheid'),
            exclude = ('UUID', 'Created_By', 'Created_Date'),
            unknown=MM.utils.RAISE
        )
        try:
            beleidsregel_aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400    
        
        
        
        oude_beleidsregel = single_object_by_uuid('BeleidsRegel', beleidsregel_op_uuid, uuid=beleidsregel_uuid)
        
        if not oude_beleidsregel:
            return {'message': f"BeleidsRegel met UUID {beleidsregel_uuid} is niet gevonden"}, 404
        
        
        beleidsregel = {**oude_beleidsregel, **beleidsregel_aanpassingen}
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(
        beleidsregel_aanpassen,
        beleidsregel['ID'],
        beleidsregel['Titel'],
        beleidsregel['Omschrijving'],
        beleidsregel['Weblink'],
        beleidsregel['Begin_Geldigheid'],
        beleidsregel['Eind_Geldigheid'],
        beleidsregel['Created_By'],
        beleidsregel['Created_Date'],
        beleidsregel['Modified_By'],
        beleidsregel['Modified_Date'])
        new_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}


