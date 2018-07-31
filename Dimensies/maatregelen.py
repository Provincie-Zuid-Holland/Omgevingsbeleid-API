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
    
class Maatregelen_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Titel = MM.fields.Str(required=True)
    Motivering = MM.fields.Str(missing=None)
    Beleids_Document = MM.fields.Str(missing=None)
    Gebied = MM.fields.UUID(missing=None, attribute='fk_Gebied')
    Verplicht_Programma = MM.fields.Str(missing=None, validate= [MM.validate.OneOf(["Ja", "Nee"])])
    Specifiek_Of_Generiek = MM.fields.Str(missing=None, validate= [MM.validate.OneOf(["Gebiedsspecifiek", "Generiek"])])
    Weblink = MM.fields.Str(missing=None)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.Str(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.Str(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)

    class Meta:
        ordered = True
        

class Maatregel(Resource):
    """Deze resource vertegenwoordigd de Beleidsregels van de provincie"""
    def get(self, maatregel_uuid=None):
        if maatregel_uuid:
            opgave = single_object_by_uuid('Maatregel', maatregel_op_uuid, uuid=maatregel_uuid)
            
            if not opgave:
                return {'message': f"Maatregel met UUID {maatregel_uuid} is niet gevonden"}, 400
            
            schema = Maatregelen_Schema()
            return(schema.dump(opgave))
        else:    
            maatregelen = objects_from_query('Maatregel', alle_maatregelen)
      
            schema = Maatregelen_Schema()
            return(schema.dump(maatregelen, many=True))

    def post(self, maatregel_uuid=None):
        if maatregel_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
        
        schema = Maatregelen_Schema( 
            exclude = ('UUID','Modified_By', 'Modified_Date'),
            unknown=MM.utils.RAISE)
        try:
            maatregel = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(maatregel_aanmaken,
        maatregel['Titel'],
        maatregel['Motivering'],
        maatregel['Beleids_Document'],
        maatregel['fk_Gebied'],
        maatregel['Verplicht_Programma'],
        maatregel['Specifiek_Of_Generiek'],
        maatregel['Weblink'],
        maatregel['Begin_Geldigheid'],
        maatregel['Eind_Geldigheid'],
        maatregel['Created_By'],
        maatregel['Created_Date'],
        maatregel['Created_By'],
        maatregel['Created_Date'])
        maatregel_uuid = cursor.fetchone()[0]

        connection.commit()
        return {"Resultaat_UUID": f"{maatregel_uuid}"}

    def patch(self, maatregel_uuid=None):
        if not maatregel_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
        patch_schema = Maatregelen_Schema(
        
            
            partial=('Titel', 'Motivering', 'Beleids_Document', 'Gebied', 'Verplicht_Programma', 'Specifiek_Of_Generiek', 'Weblink', 'Begin_Geldigheid', 'Eind_Geldigheid'),
            exclude = ('UUID', 'Created_By', 'Created_Date')
            )
        try:
            maatregel_aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        
        oude_maatregel = single_object_by_uuid('Maatregelen', maatregel_op_uuid, uuid=maatregel_uuid)
        
        if not oude_maatregel:
            return {'message': f'Maatregel met UUID {maatregel_uuid} is niet gevonden'}, 400
        
        
        maatregel = {**oude_maatregel, **maatregel_aanpassingen}
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(maatregel_aanpassen,
        maatregel['ID'],
        maatregel['Titel'],
        maatregel['Motivering'],
        maatregel['Beleids_Document'],
        maatregel['fk_Gebied'],
        maatregel['Verplicht_Programma'],
        maatregel['Specifiek_Of_Generiek'],
        maatregel['Weblink'],
        maatregel['Begin_Geldigheid'],
        maatregel['Eind_Geldigheid'],
        maatregel['Created_By'],
        maatregel['Created_Date'],
        maatregel['Modified_By'],
        maatregel['Modified_Date'])
        maatregel_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{maatregel_uuid}"}
        

