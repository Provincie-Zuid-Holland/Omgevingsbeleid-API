from flask_restful import Resource, Api, fields, marshal, reqparse, inputs, abort
import pyodbc
import marshmallow as MM
from flask import request
from globals import db_connection_settings, null_uuid
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
        with pyodbc.connect(db_connection_settings) as cnx:
            cur = cnx.cursor()
            if gebruiker_uuid:
                gebruikers = list(cur.execute(
                    'SELECT * FROM Gebruikers WHERE UUID = ?', gebruiker_uuid))

                if not gebruikers:
                    return {'message': f"Gebruiker met UUID {gebruiker_uuid} is niet gevonden"}, 400

                schema = Gebruiker_Schema(exclude=['Wachtwoord'])
                return(schema.dump(gebruikers[0]))
            else:
                gebruikers = cur.execute(
                    f"SELECT * FROM Gebruikers WHERE UUID != '{null_uuid}'")
                schema = Gebruiker_Schema(exclude=['Wachtwoord'])
                return(schema.dump(gebruikers, many=True))
