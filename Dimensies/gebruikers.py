import marshmallow as MM
from flask_restful import Resource
from flask_jwt_extended import jwt_required
import pyodbc
from globals import null_uuid, db_connection_settings


class Gebruiker_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Gebruikersnaam = MM.fields.Str(required=True)
    Wachtwoord = MM.fields.Str(missing=None)
    Rol = MM.fields.Str(missing=None)
    Status = MM.fields.Str(missing=None)
    Email = MM.fields.Str(missing=None)

    class Meta:
        table = 'Gebruikers'
        read_only = True
        ordered = True
        searchable = False


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
