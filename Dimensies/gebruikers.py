from flask_restful import Resource, Api, fields, marshal, reqparse, inputs, abort
import records
import pyodbc
import marshmallow as MM 
from flask import request

from queries import *
from helpers import single_object_by_uuid, objects_from_query, related_objects_from_query, validate_UUID
from globals import db_connection_string, db_connection_settings
from uuid import UUID
from flask_jwt_extended import jwt_required


class Gebruiker_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Gebruikersnaam = MM.fields.Str(required=True)
    Wachtwoord = MM.fields.Str(missing=None)
    Rol = MM.fields.Str(missing=None)
    Email = MM.fields.Str(missing=None)

    class Meta:
        ordered = True
    


class Gebruiker(Resource):
    """Deze resource vertegenwoordigd de Gebruikers van de applicaite"""
    @jwt_required
    def get(self, gebruiker_uuid=None):
        if gebruiker_uuid:
            gebruiker = single_object_by_uuid('Gebruikers', gebruiker_op_uuid, uuid=gebruiker_uuid)        
            
            if not gebruiker:
                return {'message': f"Gebruiker met UUID {gebruiker_uuid} is niet gevonden"}, 400
            
            schema = Gebruiker_Schema(exclude=['Wachtwoord'])
            return(schema.dump(gebruiker))
        else:    
            gebruikers = objects_from_query('Gebruikers', alle_gebruikers)
            
            schema = Gebruiker_Schema(exclude=['Wachtwoord'])
            return(schema.dump(gebruikers, many=True))
            

    # def post(self, gebruiker_uuid=None):
    #     if gebruiker_uuid:
    #         return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
    #     schema = Gebruiker_Schema(
    #         exclude = ('UUID','Wachtwoord'),
    #         unknown=MM.utils.RAISE)
    #     try:
    #         gebruiker = schema.load(request.get_json())
    #     except MM.exceptions.ValidationError as err:
    #         return err.normalized_messages(), 400
    #     connection = pyodbc.connect(db_connection_settings)
    #     cursor = connection.cursor()
    #     cursor.execute(gebruiker_aanmaken,
    #     gebruiker['Gebruikersnaam'],
    #     gebruiker['Rol'],
    #     gebruiker['Email'],)
    #     new_uuid = cursor.fetchone()[0]
        
    #     connection.commit()
    #     return {"Resultaat_UUID": f"{new_uuid}"}
    
    # def patch(self, gebruiker_uuid=None):
    #     if not gebruiker_uuid:
    #         return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
    #     patch_schema = Gebruiker_Schema(
    #         partial=('Naam', 'Rol', 'Email'),
    #         exclude = ('UUID', 'Wachtwoord'),
    #         unknown=MM.utils.RAISE
    #         )
    #     try:
    #         gebruiker_aanpassingen = patch_schema.load(request.get_json())
    #     except MM.exceptions.ValidationError as err:
    #         return err.normalized_messages(), 400    

    #     oude_gebruiker = single_object_by_uuid('Gebruikers', gebruiker_op_uuid, uuid=gebruiker_uuid)
            
    #     if not oude_gebruiker:
    #         return {'message': f"Gebruiker met UUID {gebruiker_uuid} is niet gevonden"}, 400
            
    #     gebruiker = {**oude_gebruiker, **gebruiker_aanpassingen}
        
    #     connection = pyodbc.connect(db_connection_settings)
    #     cursor = connection.cursor()
    #     cursor.execute(gebruiker_aanpassen,
    #     gebruiker['Gebruikersnaam'],
    #     gebruiker['Rol'],
    #     gebruiker['Email'],
    #     gebruiker_uuid)

        
    #     connection.commit()
    #     return {"Resultaat_UUID": f"{gebruiker_uuid}"}


