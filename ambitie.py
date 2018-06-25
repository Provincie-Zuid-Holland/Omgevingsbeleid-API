from flask_restful import Resource, Api, fields, marshal_with, reqparse, inputs
import records
import pyodbc

from queries import *
from helpers import single_object_by_uuid, objects_from_query, related_objects_from_query
from globals import db_connection_string, db_connection_settings


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
create_argparser.add_argument('Titel', type=str, help="De titel van dit object", required=True)
create_argparser.add_argument('Omschrijving', type=str, help="De omschrijving van dit object", required=True)
create_argparser.add_argument('Weblink', type=str, help="De weblink van dit object")
create_argparser.add_argument('Begin_Geldigheid', type=inputs.datetime_from_iso8601, help="De datum waarop de geldigheid van dit object ingaat", required=True)
create_argparser.add_argument('Eind_Geldigheid', type=inputs.datetime_from_iso8601, help="De datum waarop de geldigheid van dit object eindigt", required=True)

modify_argparser = reqparse.RequestParser()
modify_argparser.add_argument('Titel', type=str, help="De titel van dit object")
modify_argparser.add_argument('Omschrijving', type=str, help="De omschrijving van dit object")
modify_argparser.add_argument('Weblink', type=str, help="De weblink van dit object")
modify_argparser.add_argument('Begin_Geldigheid', type=inputs.datetime_from_iso8601, help="De datum waarop de geldigheid van dit object ingaat")
modify_argparser.add_argument('Eind_Geldigheid', type=inputs.datetime_from_iso8601, help="De datum waarop de geldigheid van dit object eindigt")


class Ambitie(Resource):
    @marshal_with(resource_fields)
    def get(self, ambitie_uuid=None):
        if ambitie_uuid:
            ambitie = single_object_by_uuid('Ambities', ambitie_op_uuid, uuid=ambitie_uuid)
            return ambitie.as_dict()
        else:    
            ambities = objects_from_query('Ambities', alle_ambities)
            return list(map(lambda ambitie: ambitie.as_dict(), ambities))

    def post(self, ambitie_uuid=None):
        if ambitie_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identifiet uit URL"}, 400
        args = create_argparser.parse_args(strict=True)
        print(args)
        return {"Placeholder": "Create"}

    def patch(self, ambitie_uuid=None):
        if not ambitie_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        args = modify_argparser.parse_args(strict=True)
        print(args)
        return {"Placeholder": f"Modify {ambitie_uuid}"}


