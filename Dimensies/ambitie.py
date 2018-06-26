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
    'Weblink': fields.String,
    'Begin_Geldigheid': fields.DateTime(dt_format='iso8601'),
    'Eind_Geldigheid': fields.DateTime(dt_format='iso8601'),
    'Created_By': fields.String,
    'Created_Date': fields.DateTime(dt_format='iso8601'),
    'Modified_By': fields.String,
    'Modified_Date': fields.DateTime(dt_format='iso8601')}

create_argparser= reqparse.RequestParser()
create_argparser.add_argument('Titel', type=str, help="{error_msg}: De titel van dit object", required=True)
create_argparser.add_argument('Omschrijving', type=str, help="{error_msg}: De omschrijving van dit object", required=True)
create_argparser.add_argument('Weblink', type=str, help="{error_msg}: De weblink van dit object")
create_argparser.add_argument('Begin_Geldigheid', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop de geldigheid van dit object ingaat", required=True)
create_argparser.add_argument('Eind_Geldigheid', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop de geldigheid van dit object eindigt", required=True)
create_argparser.add_argument('Created_By', type=str, help="{error_msg}: De gebruiker die dit object heeft aangemaakt", required=True)
create_argparser.add_argument('Created_Date', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop dit object is aangemaakt", required=True)

modify_argparser = reqparse.RequestParser()
modify_argparser.add_argument('Titel', type=str, help="{error_msg}: De titel van dit object")
modify_argparser.add_argument('Omschrijving', type=str, help="{error_msg}: De omschrijving van dit object")
modify_argparser.add_argument('Weblink', type=str, help="{error_msg}: De weblink van dit object")
modify_argparser.add_argument('Begin_Geldigheid', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop de geldigheid van dit object ingaat")
modify_argparser.add_argument('Eind_Geldigheid', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop de geldigheid van dit object eindigt")
modify_argparser.add_argument('Modified_By', type=str, help="{error_msg}: De gebruiker die dit object heeft aangepast", required=True)
modify_argparser.add_argument('Modified_Date', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop dit object is aangepast", required=True)


class Ambitie(Resource):
    """Deze resource vertegenwoordigd de Ambities van de provincie"""
    @swag_from('ambitie.yml')
    def get(self, ambitie_uuid=None):
        if ambitie_uuid:
            val_ambitie_uuid = validate_UUID(ambitie_uuid)
            
            if not val_ambitie_uuid:
                return {'message': f"Waarde {ambitie_uuid} is geen geldige UUID"}, 400
            
            ambitie = single_object_by_uuid('Ambities', ambitie_op_uuid, uuid=ambitie_uuid)
            
            if not ambitie:
                return {'message': f"Ambitie met UUID {ambitie_uuid} is niet gevonden"}, 400
            
            return marshal(ambitie.as_dict(), resource_fields)
        else:    
            ambities = objects_from_query('Ambities', alle_ambities)

            return marshal(list(map(lambda ambitie: ambitie.as_dict(), ambities)), resource_fields)

    def post(self, ambitie_uuid=None):
        if ambitie_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400

        args = create_argparser.parse_args(strict=True)
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(
        '''
        INSERT INTO Ambities (Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''',
        args.Titel,
        args.Omschrijving,
        args.Weblink,
        args.Begin_Geldigheid,
        args.Eind_Geldigheid,
        args.Created_By,
        args.Created_Date,
        args.Created_By,
        args.Created_Date)
        new_uuid = cursor.fetchone()[0]
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}
    
    def patch(self, ambitie_uuid=None):
        if not ambitie_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        args = modify_argparser.parse_args(strict=True)
        val_ambitie_uuid = validate_UUID(ambitie_uuid)
        
        if not val_ambitie_uuid:
            return {'message': f"Waarde {ambitie_uuid} is geen geldige UUID"}, 400
        
        ambitie = single_object_by_uuid('Ambities', ambitie_op_uuid, uuid=ambitie_uuid)
        
        if not ambitie:
            return {'message': f"Ambitie met UUID {ambitie_uuid} is niet gevonden"}, 400
            
        new_ambitie = ambitie.as_dict()
        for key in new_ambitie:
            if key in args and args[key]:
                new_ambitie[key] = args[key]
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(
        '''
        INSERT INTO Ambities (ID, Titel, Omschrijving, Weblink, Begin_Geldigheid, Eind_Geldigheid, Created_By, Created_Date, Modified_By, Modified_Date)
        OUTPUT inserted.UUID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''',
        new_ambitie['ID'],
        new_ambitie['Titel'],
        new_ambitie['Omschrijving'],
        new_ambitie['Weblink'],
        new_ambitie['Begin_Geldigheid'],
        new_ambitie['Eind_Geldigheid'],
        new_ambitie['Created_By'],
        new_ambitie['Created_Date'],
        new_ambitie['Modified_By'],
        new_ambitie['Modified_Date'])
        new_uuid = cursor.fetchone()[0]
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}


