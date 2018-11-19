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

class Koppelingen_Schema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Omschrijving = MM.fields.Str(missing="")
    
class BeleidsBeslissing_CreateSchema(MM.Schema):
    UUID = MM.fields.UUID(required=True)
    Eigenaar_1 = MM.fields.Str(required=True)
    Eigenaar_2 = MM.fields.Str(required=True)
    Portefeuillehouder = MM.fields.Str(required=True)
    Status = MM.fields.Str(required=True)
    Titel = MM.fields.Str(required=True)
    Omschrijving_Keuze = MM.fields.Str()
    Omschrijving_Werking = MM.fields.Str()
    Motivering = MM.fields.Str()
    Aanleiding = MM.fields.Str()
    Afweging = MM.fields.Str()
    Verordening_Realisatie = MM.fields.Str()
    # Vanaf hier hebben we het over omgevingsbeleid objecten
    WerkingsGebieden = MM.fields.Nested(Koppelingen_Schema, many=True, default=[])
    # BeleidsRelaties = MM.fields.Nested(Koppelingen_Schema, many=True, default=[])
    Verordening = MM.fields.Nested(Koppelingen_Schema, many=True,  default=[])
    Maatregelen = MM.fields.Nested(Koppelingen_Schema, many=True,  default=[])
    BeleidsRegels = MM.fields.Nested(Koppelingen_Schema, many=True,  default=[])
    Themas = MM.fields.Nested(Koppelingen_Schema, many=True, default=[])
    Ambities = MM.fields.Nested(Koppelingen_Schema, many=True, default=[])
    Doelen = MM.fields.Nested(Koppelingen_Schema, many=True, default=[])
    ProvincialeBelangen = MM.fields.Nested(Koppelingen_Schema, many=True, default=[])
    Opgaven = MM.fields.Nested(Koppelingen_Schema, many=True, default=[])
    # Vanaf hier niet meer
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.Str(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.Str(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)
    
    @MM.validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        unknown = [k for k in original_data.keys() if k not in self.fields]
        # unknown = set(original_data) - set(self.fields)
        if unknown:
            raise MM.ValidationError('Unknown field name', list(unknown)[0])
    
    class Meta:
        ordered = True
        

OMGEVINGSBELEID_FIELDS = ['WerkingsGebieden', 'BeleidsRelaties' , 'Verordening', 'Maatregelen' 
, 'BeleidsRegels', 'Themas', 'Ambities', 'Doelen', 'ProvincialeBelangen', 'Opgaven']


class BeleidsBeslissing(Resource):
    """Deze resource vertegenwoordigd de Beleidsregels van de provincie"""
    # @swag_from('provinciaalbelang.yml')
    def get(self, beleidsbeslissing_uuid=None):
        if beleidsbeslissing_uuid:
            val_beleidsbeslissing_uuid = validate_UUID(beleidsbeslissing_uuid)
            
            if not val_beleidsbeslissing_uuid:
                return {'message': f"Waarde {beleidsbeslissing_uuid} is geen geldige UUID"}, 400
            
            beleidsbeslissing = single_object_by_uuid('BeleidsBeslissing', beleidsbeslissing_op_uuid, uuid=beleidsbeslissing_uuid)
            
            if not beleidsbeslissing:
                return {'message': f"BeleidsBeslissing met UUID {beleidsbeslissing_uuid} is niet gevonden"}, 400
            
            flat_obs = flatten_obs(beleidsbeslissing_uuid)
            beleidsbeslissing = {**flat_obs, **beleidsbeslissing.as_dict()}
            schema = BeleidsBeslissing_CreateSchema()
            return(schema.dump(beleidsbeslissing))
        else:    
            beleidsbeslissingen = objects_from_query('BeleidsBeslissing', alle_beleidsbeslissingen)
            beleidsbeslissingen = map(lambda bb: {**flatten_obs(bb['UUID']), **bb.as_dict()}, beleidsbeslissingen)
            schema = BeleidsBeslissing_CreateSchema()
            return(schema.dump(beleidsbeslissingen, many=True))

    def post(self, beleidsbeslissing_uuid=None):
        if beleidsbeslissing_uuid:
            return {'message': "Methode POST niet geldig op een enkel object, verwijder identiteit uit URL"}, 400
        
        schema = BeleidsBeslissing_CreateSchema(
            exclude=('UUID','Modified_By', 'Modified_Date'))
        
        try:
            beleidsbeslissing = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400
        
        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(beleidsbeslissing_aanmaken,
        beleidsbeslissing['Eigenaar_1'],
        beleidsbeslissing['Eigenaar_2'],
        beleidsbeslissing['Portefeuillehouder'],
        beleidsbeslissing['Status'],
        beleidsbeslissing['Titel'],
        beleidsbeslissing['Omschrijving_Keuze'],
        beleidsbeslissing['Omschrijving_Werking'],
        beleidsbeslissing['Motivering'],
        beleidsbeslissing['Aanleiding'],
        beleidsbeslissing['Afweging'],
        beleidsbeslissing['Verordening_Realisatie'],
        beleidsbeslissing['Begin_Geldigheid'],
        beleidsbeslissing['Eind_Geldigheid'],
        beleidsbeslissing['Created_By'],
        beleidsbeslissing['Created_Date'],
        beleidsbeslissing['Created_By'],
        beleidsbeslissing['Created_Date'])
        beleidsbeslissing_uuid = cursor.fetchone()[0]
        
        ob_flat = {}
        for field in OMGEVINGSBELEID_FIELDS:
            if field in beleidsbeslissing:
                ob_flat[field] = beleidsbeslissing[field]
            else:
                ob_flat[field]= []
        omgevingsbeleid_rows = deflatten_obs(ob_flat)
        for row in omgevingsbeleid_rows:
            try:
                cursor.execute(omgevingsbeleid_aanmaken,
                beleidsbeslissing_uuid,
                row['WerkingsGebieden']['UUID'],
                row['Verordening']['UUID'],
                row['Maatregelen']['UUID'],
                row['BeleidsRegels']['UUID'],
                row['Themas']['UUID'],
                row['Ambities']['UUID'],
                row['Doelen']['UUID'],
                row['ProvincialeBelangen']['UUID'],
                row['Opgaven']['UUID'],
                row['WerkingsGebieden']['Omschrijving'],
                row['Verordening']['Omschrijving'],
                row['Maatregelen']['Omschrijving'],
                row['BeleidsRegels']['Omschrijving'],
                row['Themas']['Omschrijving'],
                row['Ambities']['Omschrijving'],
                row['Doelen']['Omschrijving'],
                row['ProvincialeBelangen']['Omschrijving'],
                row['Opgaven']['Omschrijving'],
                None,
                None,
                None,
                None,
                None,
                None)
            
            except pyodbc.IntegrityError as odbcex:
                connection.close()                
                pattern = re.compile('FK_\w+_(\w+)')
                match = pattern.search(odbcex.args[1]).group(1)
                return {"Database error":f'Unknown UUID for object {match}'}, 400
                
            except Exception as odbcex:
                connection.close()
                return odbcex, 400

        connection.commit()
        return {"Resultaat_UUID": f"{beleidsbeslissing_uuid}"}
    
    def patch(self, beleidsbeslissing_uuid=None):
        if not beleidsbeslissing_uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400
        
        patch_schema = BeleidsBeslissing_CreateSchema(exclude=['UUID', 'Created_Date', 'Created_By'],                                                    
                                                      partial=('Eigenaar_1',
                                                            'Eigenaar_2',
                                                            'Portefeuillehouder',
                                                            'Status',
                                                            'Titel',
                                                            'Omschrijving_Keuze',
                                                            'Omschrijving_Werking',
                                                            'Motivering',
                                                            'Aanleiding',
                                                            'Afweging',
                                                            'Verordening_Realisatie',
                                                            'Begin_Geldigheid',
                                                            'Eind_Geldigheid'
                                                            ))
        schema = BeleidsBeslissing_CreateSchema()
        try:
            beleidsbeslissing_aanpassingen = patch_schema.load(request.get_json())
            beleidsbeslissing_oud = single_object_by_uuid('BeleidsBeslissing', beleidsbeslissing_op_uuid, uuid=beleidsbeslissing_uuid).as_dict()
            
            for key in beleidsbeslissing_aanpassingen:
                beleidsbeslissing_oud[key] = beleidsbeslissing_aanpassingen[key]
            
            flat_obs = flatten_obs(beleidsbeslissing_uuid)
            beleidsbeslissing_oud = {**flat_obs, **beleidsbeslissing_oud}
            
            connection = pyodbc.connect(db_connection_settings)
            cursor = connection.cursor()
            cursor.execute(beleidsbeslissing_aanpassen,
            beleidsbeslissing_oud['ID'],
            beleidsbeslissing_oud['Eigenaar_1'],
            beleidsbeslissing_oud['Eigenaar_2'],
            beleidsbeslissing_oud['Portefeuillehouder'],
            beleidsbeslissing_oud['Status'],
            beleidsbeslissing_oud['Titel'],
            beleidsbeslissing_oud['Omschrijving_Keuze'],
            beleidsbeslissing_oud['Omschrijving_Werking'],
            beleidsbeslissing_oud['Motivering'],
            beleidsbeslissing_oud['Aanleiding'],
            beleidsbeslissing_oud['Afweging'],
            beleidsbeslissing_oud['Verordening_Realisatie'],
            beleidsbeslissing_oud['Begin_Geldigheid'],
            beleidsbeslissing_oud['Eind_Geldigheid'],
            beleidsbeslissing_oud['Created_By'],
            beleidsbeslissing_oud['Created_Date'],
            beleidsbeslissing_oud['Modified_By'],
            beleidsbeslissing_oud['Modified_Date'])
            beleidsbeslissing_uuid = cursor.fetchone()[0]
            
            ob_flat = {}
            for field in OMGEVINGSBELEID_FIELDS:
                if field in beleidsbeslissing_oud:
                    ob_flat[field] = beleidsbeslissing_oud[field]
                else:
                    ob_flat[field]= []
            omgevingsbeleid_rows = deflatten_obs(ob_flat)
            for row in omgevingsbeleid_rows:
                try:
                    cursor.execute(omgevingsbeleid_aanmaken,
                    beleidsbeslissing_uuid,
                    row['WerkingsGebieden']['UUID'],
                    # row['BeleidsRelaties']['UUID'],
                    row['Verorderingen']['UUID'],
                    row['Maatregelen']['UUID'],
                    row['BeleidsRegels']['UUID'],
                    row['Themas']['UUID'],
                    row['Ambities']['UUID'],
                    row['Doelen']['UUID'],
                    row['ProvincialeBelangen']['UUID'],
                    row['Opgaven']['UUID'],
                    row['WerkingsGebieden']['Omschrijving'],
                    # row['BeleidsRelaties']['Omschrijving'],
                    row['Verorderingen']['Omschrijving'],
                    row['Maatregelen']['Omschrijving'],
                    row['BeleidsRegels']['Omschrijving'],
                    row['Themas']['Omschrijving'],
                    row['Ambities']['Omschrijving'],
                    row['Doelen']['Omschrijving'],
                    row['ProvincialeBelangen']['Omschrijving'],
                    row['Opgaven']['Omschrijving'],
                    None,
                    None,
                    None,
                    None,
                    None,
                    None)
            
                except pyodbc.IntegrityError as odbcex:
                    connection.close()                
                    pattern = re.compile('FK_\w+_(\w+)')
                    match = pattern.search(odbcex.args[1]).group(1)
                    return {"Database error":f'Unknown UUID for object {match}'}, 400
                    
                except Exception as odbcex:
                    connection.close()
                    return {"Database error":str(odbcex)}, 400

            connection.commit()
             
            return {"Resultaat_UUID": f"{beleidsbeslissing_uuid}"}
            
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400


