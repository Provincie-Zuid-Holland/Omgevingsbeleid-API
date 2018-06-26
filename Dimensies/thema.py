from flask_restful import Resource, Api, fields, marshal, reqparse, inputs, abort
import records
import pyodbc
from flasgger import swag_from

from queries import *
from helpers import single_object_by_uuid, objects_from_query, related_objects_from_query, validate_UUID
from globals import db_connection_string, db_connection_settings
from uuid import UUID

resource_fields = {
    'UUID': fields.String,
    'Titel': fields.String,
    'Omschrijving':fields.String,
    'Begin_Geldigheid': fields.DateTime(dt_format='iso8601'),
    'Eind_Geldigheid': fields.DateTime(dt_format='iso8601'),
    'Created_By': fields.String,
    'Created_Date': fields.DateTime(dt_format='iso8601'),
    'Modified_By': fields.String,
    'Modified_Date': fields.DateTime(dt_format='iso8601')}

create_argparser= reqparse.RequestParser()
create_argparser.add_argument('Titel', type=str, help="{error_msg}: De titel van dit object", required=True)
create_argparser.add_argument('Omschrijving', type=str, help="{error_msg}: De omschrijving van dit object", required=True)
create_argparser.add_argument('Begin_Geldigheid', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop de geldigheid van dit object ingaat", required=True)
create_argparser.add_argument('Eind_Geldigheid', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop de geldigheid van dit object eindigt", required=True)
create_argparser.add_argument('Created_By', type=str, help="{error_msg}: De gebruiker die dit object heeft aangemaakt", required=True)
create_argparser.add_argument('Created_Date', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop dit object is aangemaakt", required=True)

modify_argparser = reqparse.RequestParser()
modify_argparser.add_argument('Titel', type=str, help="{error_msg}: De titel van dit object")
modify_argparser.add_argument('Omschrijving', type=str, help="{error_msg}: De omschrijving van dit object")
modify_argparser.add_argument('Begin_Geldigheid', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop de geldigheid van dit object ingaat")
modify_argparser.add_argument('Eind_Geldigheid', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop de geldigheid van dit object eindigt")
modify_argparser.add_argument('Modified_By', type=str, help="{error_msg}: De gebruiker die dit object heeft aangepast", required=True)
modify_argparser.add_argument('Modified_Date', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop dit object is aangepast", required=True)


class Thema(Resource):
    """Deze resource vertegenwoordigd de Beleidsregels van de provincie"""
    @swag_from('thema.yml')
    def get(self, thema_uuid=None):
        if thema_uuid:
            val_thema_uuid = validate_UUID(thema_uuid)
            
            if not val_thema_uuid:
                return {'message': f"Waarde {thema_uuid} is geen geldige UUID"}, 400
            
            thema = single_object_by_uuid('Thema', thema_op_uuid, uuid=thema_uuid)
            
            if not thema:
                return {'message': f"Thema met UUID {thema_uuid} is niet gevonden"}, 400
            
            return marshal(thema.as_dict(), resource_fields)
        else:    
            themas = objects_from_query('Thema', alle_themas)

            return marshal(list(map(lambda thema: thema.as_dict(), themas)), resource_fields)

    def post(self, thema_uuid=None):
        if thema_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400

        args = create_argparser.parse_args(strict=True)
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(thema_aanmaken,
        args.Titel,
        args.Omschrijving,
        args.Begin_Geldigheid,
        args.Eind_Geldigheid,
        args.Created_By,
        args.Created_Date,
        args.Created_By,
        args.Created_Date)
        new_uuid = cursor.fetchone()[0]
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}
    
    def patch(self, thema_uuid=None):
        if not thema_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        args = modify_argparser.parse_args(strict=True)
        val_thema_uuid = validate_UUID(thema_uuid)
        
        if not val_thema_uuid:
            return {'message': f"Waarde {thema_uuid} is geen geldige UUID"}, 400
        
        thema = single_object_by_uuid('Thema', thema_op_uuid, uuid=thema_uuid)
        
        if not thema:
            return {'message': f"Thema met UUID {thema_uuid} is niet gevonden"}, 400
            
        new_thema = thema.as_dict()
        for key in new_thema:
            if key in args and args[key]:
                new_thema[key] = args[key]
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(
        thema_aanpassen,
        new_thema['ID'],
        new_thema['Titel'],
        new_thema['Omschrijving'],
        new_thema['Begin_Geldigheid'],
        new_thema['Eind_Geldigheid'],
        new_thema['Created_By'],
        new_thema['Created_Date'],
        new_thema['Modified_By'],
        new_thema['Modified_Date'])
        new_uuid = cursor.fetchone()[0]
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}


