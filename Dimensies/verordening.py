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


class Verordening_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Titel = MM.fields.Str(required=True)
    Omschrijving = MM.fields.Str(missing=None)
    Status = MM.fields.Str(required=True)
    Type = MM.fields.Str(required=True, validate= [MM.validate.OneOf(['Hoofdstuk', 'Afdeling', 'Paragraaf', 'Artikel']),])
    Volgnummer = MM.fields.Str(required=True)
    Werkingsgebied = MM.fields.UUID(missing=None, attribute= 'fk_Werkingsgebied')
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.Str(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.Str(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)

    class Meta:
        ordered = True
    


class Verordening(Resource):
    """Deze resource vertegenwoordigd de Ambities van de provincie"""
    # @swag_from('verordening.yml')
    def get(self, verordening_uuid=None):
        if verordening_uuid:
            verordening = single_object_by_uuid('Verordeningen', verordening_op_uuid, uuid=verordening_uuid)        
            
            if not verordening:
                return {'message': f"Verordening met UUID {verordening_uuid} is niet gevonden"}, 400
            
            schema = Verordening_Schema()
            return(schema.dump(verordening))
        else:    
            verordenings = objects_from_query('Verordeningen', alle_verordeningen)
            
            schema = Verordening_Schema()
            return(schema.dump(verordenings, many=True))
            

    def post(self, verordening_uuid=None):
        if verordening_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
        schema = Verordening_Schema(
            exclude = ('UUID','Modified_By', 'Modified_Date'),
            unknown=MM.utils.RAISE)
        try:
            verordening = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(verordening_aanmaken,
        verordening['Titel'],
        verordening['Omschrijving'],
        verordening['Status'],
        verordening['Type'],
        verordening['Volgnummer'],
        verordening['fk_Werkingsgebied'],
        verordening['Begin_Geldigheid'],
        verordening['Eind_Geldigheid'],
        verordening['Created_By'],
        verordening['Created_Date'],
        verordening['Created_By'],
        verordening['Created_Date'])
        new_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}
    
    def patch(self, verordening_uuid=None):
        if not verordening_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
        patch_schema = Verordening_Schema(
            partial=('Titel', 'Omschrijving', 'Status', 'Type', 'Volgnummer', 'Werkingsgebied', 'Begin_Geldigheid', 'Eind_Geldigheid'),
            exclude = ('UUID', 'Created_By', 'Created_Date'),
            unknown=MM.utils.RAISE
            )
        try:
            verordening_aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400    

        oude_verordening = single_object_by_uuid('Verordenings', verordening_op_uuid, uuid=verordening_uuid)
            
        if not oude_verordening:
            return {'message': f"Verordening met UUID {verordening_uuid} is niet gevonden"}, 400
            
        verordening = {**oude_verordening, **verordening_aanpassingen}
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(verordening_aanpassen,
        verordening['ID'],
        verordening['Titel'],
        verordening['Omschrijving'],
        verordening['Status'],
        verordening['Type'],
        verordening['Volgnummer'],
        verordening['fk_Werkingsgebied'],
        verordening['Begin_Geldigheid'],
        verordening['Eind_Geldigheid'],
        verordening['Created_By'],
        verordening['Created_Date'],
        verordening['Modified_By'],
        verordening['Modified_Date'])
        verordening_uuid = cursor.fetchone()[0]
        
        connection.commit()
        return {"Resultaat_UUID": f"{verordening_uuid}"}


