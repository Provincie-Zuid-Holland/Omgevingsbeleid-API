from flask_restful import Resource, Api, fields, marshal, reqparse, inputs, abort
import records
import pyodbc
from flasgger import swag_from
import marshmallow as MM 
from flask import request
import re

from queries import *
from helpers import single_object_by_uuid, objects_from_query, related_objects_from_query, validate_UUID
from globals import db_connection_string, db_connection_settings
from uuid import UUID


class BeleidsRelatie_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Van_Beleidsbeslissing = MM.fields.UUID(required=True)
    Naar_Beleidsbeslissing = MM.fields.UUID(required=True)
    Omschrijving = MM.fields.Str(missing=None)
    Status = MM.fields.Str(required=True, validate= [MM.validate.OneOf(['Open', 'Akkoord', 'NietAkkoord']),])
    Aanvraag_Datum = MM.fields.DateTime(format='iso', required=True)
    Datum_Akkoord = MM.fields.DateTime(format='iso', allow_none=True)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.Str(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.Str(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)

    class Meta:
        ordered = True
    


class BeleidsRelatie(Resource):
    """Deze resource vertegenwoordigd de Ambities van de provincie"""
    def get(self, beleidsrelatie_uuid=None):
        if beleidsrelatie_uuid:
            beleidsrelatie = single_object_by_uuid('BeleidsRelaties', beleidsrelatie_op_uuid, uuid=beleidsrelatie_uuid)        
            
            if not beleidsrelatie:
                return {'message': f"BeleidsRelatie met UUID {beleidsrelatie_uuid} is niet gevonden"}, 400
            
            schema = BeleidsRelatie_Schema()
            return(schema.dump(beleidsrelatie))
        else:    
            beleidsrelaties = objects_from_query('BeleidsRelaties', alle_beleidsrelaties)
            
            schema = BeleidsRelatie_Schema()
            return(schema.dump(beleidsrelaties, many=True))
            

    def post(self, beleidsrelatie_uuid=None):
        if beleidsrelatie_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
        schema = BeleidsRelatie_Schema(
            exclude = ('UUID','Modified_By', 'Modified_Date'),
            unknown=MM.utils.RAISE)
        try:
            beleidsrelatie = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        
        # Check of er geen zelfkoppeling plaatsvind
        if beleidsrelatie['Van_Beleidsbeslissing'] == beleidsrelatie['Naar_Beleidsbeslissing']:
            return {'message': "Een beleidsbesslising kan niet naar zichzelf koppelen"}, 400
        
        # Check of er al een relatie de andere kant op bestaat
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(check_beleidsrelatie,
            beleidsrelatie['Van_Beleidsbeslissing'],
            beleidsrelatie['Naar_Beleidsbeslissing'],
            beleidsrelatie['Van_Beleidsbeslissing'],
            beleidsrelatie['Naar_Beleidsbeslissing'])
        
        conflict_row = cursor.fetchone()

        if conflict_row:
            return {'message': 'Er bestaat al een relatie tussen deze objecten',
                    'UUID': conflict_row.UUID}, 400 
        
        
        if beleidsrelatie['Status'] != 'Open':
            return {'Status':["Must be 'Open'",]}, 400
            
        
        try:
            connection = pyodbc.connect(db_connection_settings)
            cursor = connection.cursor()
            cursor.execute(beleidsrelatie_aanmaken,
            beleidsrelatie['Van_Beleidsbeslissing'],
            beleidsrelatie['Naar_Beleidsbeslissing'],
            beleidsrelatie['Omschrijving'],
            beleidsrelatie['Status'],
            beleidsrelatie['Aanvraag_Datum'],
            beleidsrelatie['Datum_Akkoord'],
            beleidsrelatie['Begin_Geldigheid'],
            beleidsrelatie['Eind_Geldigheid'],
            beleidsrelatie['Created_By'],
            beleidsrelatie['Created_Date'],
            beleidsrelatie['Created_By'],
            beleidsrelatie['Created_Date'])
            new_uuid = cursor.fetchone()[0]
        
        except pyodbc.IntegrityError as odbcex:
            connection.close()                
            pattern = re.compile('FK_\w+_(\w+)')
            match = pattern.search(odbcex.args[1]).group(1)
            if match:
                return {"Database error":f'Unknown UUID for object {match}'}, 400
            else:
                return {"Database error":str(odbcex)}, 400
        
        except Exception as odbcex:
            connection.close()
            return {"Database error":str(odbcex)}, 400
        
        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}
    
    def patch(self, beleidsrelatie_uuid=None):
        if not beleidsrelatie_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
        patch_schema = BeleidsRelatie_Schema(
            partial=('Omschrijving', 'Aanvraag_Datum', 'Begin_Geldigheid', 'Eind_Geldigheid', 'Status', 'Datum_Akkoord'),
            exclude = ('UUID', 'Created_By', 'Created_Date', 'Van_Beleidsbeslissing', 'Naar_Beleidsbeslissing'),
            unknown=MM.utils.RAISE
            )
        try:
            beleidsrelatie_aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400    

        oude_beleidsrelatie = single_object_by_uuid('BeleidsRelaties', beleidsrelatie_op_uuid, uuid=beleidsrelatie_uuid)
            
        if not oude_beleidsrelatie:
            return {'message': f"BeleidsRelatie met UUID {beleidsrelatie_uuid} is niet gevonden"}, 400
            
        beleidsrelatie = {**oude_beleidsrelatie, **beleidsrelatie_aanpassingen}
        
        try:
            connection = pyodbc.connect(db_connection_settings)
            cursor = connection.cursor()
            cursor.execute(beleidsrelatie_aanpassen,
            beleidsrelatie['ID'],
            beleidsrelatie['Van_Beleidsbeslissing'],
            beleidsrelatie['Naar_Beleidsbeslissing'],
            beleidsrelatie['Omschrijving'],
            beleidsrelatie['Status'],
            beleidsrelatie['Aanvraag_Datum'],
            beleidsrelatie['Datum_Akkoord'],
            beleidsrelatie['Begin_Geldigheid'],
            beleidsrelatie['Eind_Geldigheid'],
            beleidsrelatie['Created_By'],
            beleidsrelatie['Created_Date'],
            beleidsrelatie['Modified_By'],
            beleidsrelatie['Modified_Date'])
            beleidsrelatie_uuid = cursor.fetchone()[0]
        
        except pyodbc.IntegrityError as odbcex:
            connection.close()                
            pattern = re.compile('FK_\w+_(\w+)')
            match = pattern.search(odbcex.args[1]).group(1)
            if match:
                return {"Database error":f'Unknown UUID for object {match}'}, 400
            else:
                return {"Database error":str(odbcex)}, 400
        
        except Exception as odbcex:
            connection.close()
            return {"Database error":str(odbcex)}, 400
        
        connection.commit()
        return {"Resultaat_UUID": f"{beleidsrelatie_uuid}"}


