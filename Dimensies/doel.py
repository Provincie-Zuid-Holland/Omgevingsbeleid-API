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
create_argparser.add_argument('Omschrijving', type=str, help="{error_msg}: De omschrijving van dit object", nullable=True)
create_argparser.add_argument('Weblink', type=str, help="{error_msg}: De weblink van dit object")
create_argparser.add_argument('Begin_Geldigheid', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop de geldigheid van dit object ingaat")
create_argparser.add_argument('Eind_Geldigheid', type=inputs.datetime_from_iso8601, help="{error_msg}: De datum waarop de geldigheid van dit object eindigt")
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


class Doel(Resource):
    """Deze resource vertegenwoordigd de Beleidsregels van de provincie"""
    @swag_from('doel.yml')
    def get(self, doel_uuid=None):
        if doel_uuid:
            val_doel_uuid = validate_UUID(doel_uuid)
            
            if not val_doel_uuid:
                return {'message': f"Waarde {doel_uuid} is geen geldige UUID"}, 400
            
            doel = single_object_by_uuid('Doel', doel_op_uuid, uuid=doel_uuid)
            
            if not doel:
                return {'message': f"Doel met UUID {doel_uuid} is niet gevonden"}, 400
            
            return marshal(doel.as_dict(), resource_fields)
        else:    
            doelen = objects_from_query('Doel', alle_doelen)

            return marshal(list(map(lambda doel: doel.as_dict(), doelen)), resource_fields)

    def post(self, doel_uuid=None):
        if doel_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400

        args = create_argparser.parse_args(strict=True)
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(doel_aanmaken,
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
    
    def patch(self, doel_uuid=None):
        if not doel_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        args = modify_argparser.parse_args(strict=True)
        val_doel_uuid = validate_UUID(doel_uuid)
        
        if not val_doel_uuid:
            return {'message': f"Waarde {doel_uuid} is geen geldige UUID"}, 400
        
        doel = single_object_by_uuid('BeleidsRegel', doel_op_uuid, uuid=doel_uuid)
        
        if not doel:
            return {'message': f"BeleidsRegel met UUID {doel_uuid} is niet gevonden"}, 400
            
        new_doel = doel.as_dict()
        for key in new_doel:
            if key in args and args[key]:
                new_doel[key] = args[key]
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(
        doel_aanpassen,
        new_doel['ID'],
        new_doel['Titel'],
        new_doel['Omschrijving'],
        new_doel['Weblink'],
        new_doel['Begin_Geldigheid'],
        new_doel['Eind_Geldigheid'],
        new_doel['Created_By'],
        new_doel['Created_Date'],
        new_doel['Modified_By'],
        new_doel['Modified_Date'])
        new_uuid = cursor.fetchone()[0]
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}


