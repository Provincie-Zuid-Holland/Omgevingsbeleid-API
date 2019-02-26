from flask_restful import Resource
import records
import pyodbc
from flask import request
import marshmallow as MM
from operator import eq
from globals import db_connection_string, db_connection_settings
import marshmallow as MM
import re

# from .dimensie import Dimensie


class Dimensie_Schema(MM.Schema):
    """
    Schema voor de standaard velden van een dimensie
    """
    UUID = MM.fields.UUID(required=True)
    Begin_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Eind_Geldigheid = MM.fields.DateTime(format='iso', required=True)
    Created_By = MM.fields.UUID(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.UUID(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)
    
    class Meta:
        ordered = True

# Helper methods

def objects_from_query(query):
        """
        Verkrijg alle objecten uit een table
        """
        db = records.Database(db_connection_string)
        return db.query(query)

class DimensieList(Resource):
    # Velden die niet in een POST request gestuurd mogen worden
    _excluded_post_fields = ['UUID', 'Modified_By', 'Modified_Date']

    # Veld dat dient als identificatie
    _identifier_field = 'UUID'

    # def __new__(cls, tableschema, tablename_all, tablename_actueel):
    #     # Dynamische documentatie generatie
    #     cls.get.__func__.__doc__ = self.get.__func__.__doc__.format(dimensie_naams=tablename_all, dimensie_schema=tableschema.__name__) 


    def __init__(self, tableschema, tablename_all, tablename_actueel):
        self.all_query = f'SELECT * FROM {tablename_actueel}'
        self._tableschema = tableschema

        # Is het gegeven schema een superset van Dimensie_Schema?
        required_fields = Dimensie_Schema().fields.keys()
        schema_fields = tableschema().fields.keys()
        assert all([field in schema_fields for field in required_fields]), "Gegeven schema is geen superset van Dimensie Schema"

        # POST Queries worden met deze argumenten gemaakt
        self.query_fields = []
        # filter alle velden, als een veld gebruik maakt van een 'attribute' naam gebruik die naam dan
        for fieldkey, fieldobj in tableschema().fields.items():
            if fieldkey == self._identifier_field: continue
            if fieldobj.attribute:
                self.query_fields.append(fieldobj.attribute)
            else:
                self.query_fields.append(fieldkey)

        create_fields_list = ', '.join(self.query_fields)
        create_parameter_marks = ', '.join(['?' for _ in self.query_fields])

        self.create_query = f'''INSERT INTO {tablename_all}
            ({create_fields_list})
            OUTPUT inserted.UUID
            VALUES ({create_parameter_marks})'''


    def get(self):
        """
        GET endpoint voor {dimensie_naams}.
        ---
        description: Verkrijg een lijst van alle fungerende {dimensie_naams}
        responses:
            200:
                description: Succesvolle request
                content:
                    application/json:
                        schema:
                            type: array
                            items: {dimensie_schema}
            404:
                description: Foutieve request
                content:
                    application/json:
                        schema: 
                            type: object
                            properties:
                                message:
                                    type: string
        """
        # Alle objecten verkrijgen
        dimensie_objecten = objects_from_query(self.all_query)
        schema = self._tableschema()
        return(schema.dump(dimensie_objecten, many=True))
    
    def post(self):
        """
        POST endpoint voor deze dimensie.
        ---
        description: Creeër een nieuw dimensie object
        responses:
            200:
                description: Object succesvol aangemaakt
                content:
                    application/json:
                        schema: Ambitie_Schema
            400:
                description: Foutieve request
                content:
                    application/json:
                        schema: 
                            type: object
                            properties:
                                message:
                                    type: string
        """ 
        try:
            schema = self._tableschema(
                exclude=self._excluded_post_fields,
                unknown=MM.utils.RAISE)

        except ValueError:
            return {'message': 'Server fout in endpoint, neem contact op met administrator'}, 500

        try:
            dim_object = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        # Modification date is hetzelfde als de created date want we maken dit object nieuw aan
        dim_object['Modified_By'] = dim_object['Created_By']
        dim_object['Modified_Date'] = dim_object['Created_Date']
        try:
            values = [dim_object[k] for k in self.query_fields]
        except KeyError as e:
            # Als deze error voorkomt is er iets mis met de schema's
            return {'message': f'Schemafout voor attribuut: {e}. Neem contact op met de administrator.'}, 400

        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(self.create_query, *values)
                new_uuid = cursor.fetchone()[0]
            except pyodbc.IntegrityError as e:
                pattern = re.compile(r'FK_\w+_(\w+)')
                match = pattern.search(e.args[-1]).group(1)
                if match:
                    return {'message': f'Database integriteitsfout, een identifier van een "{match}" object is niet geldig'}, 404
                else:
                    return {'message': 'Database integriteitsfout'}, 400
            except pyodbc.DatabaseError as e:
                    return {'message': f'Database fout, neem contact op met de systeembeheerder:[{e}]'}, 400
            connection.commit()
        
        return {"Resultaat_UUID": f"{new_uuid}"}


class Dimensie(Resource):
    """
    Een enkel dimensie object met bijbehorend lees/schrijf gedrag.
    """
    # Veld dat dient als identificatie
    _identifier_field = 'UUID'

    # Velden die altijd aanwezig zullen zijn
    _general_fields = ['Begin_Geldigheid',
                       'Eind_Geldigheid',
                       'Created_By',
                       'Created_Date',
                       'Modified_By',
                       'Modified_Date']

    # Velden die niet in een PATCH request gestuurd mogen worden
    _excluded_patch_fields = ['UUID', 'Created_By', 'Created_Date']

    def __init__(self, tableschema, tablename_all, tablename_actueel=None):
        self._tablename_all = tablename_all

        if tablename_actueel:
            self._tablename_actueel = tablename_actueel
        else:
            self._tablename_actueel = tablename_all

        # Is het gegeven schema een superset van Dimensie_Schema?
        required_fields = Dimensie_Schema().fields.keys()
        schema_fields = tableschema().fields.keys()
        # Dit checkt of Dimensie_Schema geërft wordt
        assert all([field in schema_fields for field in required_fields]), "Gegeven schema is geen superset van Dimensie Schema"
        
        # Partial velden voor de PATCH
        self._partial_fields = [field for field in schema_fields if field not in self._general_fields]

        # Bouw hier de queries op
        self._tableschema = tableschema
        self.uuid_query = f'SELECT * FROM {tablename_all} WHERE UUID=:uuid'
        self.all_query = f'SELECT * FROM {tablename_actueel}'
        

        self.query_fields = list(filter(lambda fieldname: not(eq(fieldname, self._identifier_field)), schema_fields))

        # PATCH Queries are build using this list (preserving order)
        self.update_fields = self.query_fields + ['ID']
        
        update_fields_list = ', '.join(self.update_fields)
        update_parameter_marks = ', '.join(['?' for _ in self.update_fields])

        self.update_query = f'''INSERT INTO {tablename_all}
            ({update_fields_list})
            OUTPUT inserted.UUID
            VALUES ({update_parameter_marks})'''

    def single_object_by_uuid(self, uuid):
        """
        Verkrijg een enkel object op basis van UUID
        """
        db = records.Database(db_connection_string)
        return db.query(self.uuid_query, uuid=uuid).first()


    def get(self, uuid):
        """
        GET endpoint voor deze dimensie.
        ---
        description: Verkrijg een object op basis van UUID
        parameters:
            - in: path
              name: uuid
              description: De UUID van het te verkrijgen object
              schema:
                type: string
                format: uuid
        responses:
            200:
                description: Succesvolle GET
                content:
                    application/json:
                        schema: Ambitie_Schema
            404:
                description: Object met dit UUID niet gevonden
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                message:
                                    type: string
        """
        # Een enkel object verkrijgen
        dimensie_object = self.single_object_by_uuid(uuid)

        if not dimensie_object:
            return {'message': f"Object met identifier {uuid} is niet gevonden in table {self._tablename_all}"}, 404

        schema = self._tableschema()
        return(schema.dump(dimensie_object))
        

    def patch(self, uuid=None):
        """
        PATCH endpoint voor deze dimensie.
        ---
        description: Wijzig een object op basis van UUID
        parameters:
            - in: path
              name: uuid
              description: De UUID van het te wijzigen object
              schema:
                type: string
                format: uuid
        responses:
            200:
                description: Object succesvol is gewijzigd
                content:
                    application/json:
                        schema: 
                           type: object
                           properties:
                              message: 
                                type: string
            404:
                description: Foutieve request
                content:
                    application/json:
                        schema: 
                           type: object
                           properties:
                              message: 
                                type: string
        """
        if not uuid:
            return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan URL"}, 400
        try:
            patch_schema = self._tableschema(
                exclude = self._excluded_patch_fields,
                partial = self._partial_fields + ['Begin_Geldigheid', 'Eind_Geldigheid'],
                unknown = MM.utils.RAISE)

        except ValueError:
            return {'message': 'Server fout in endpoint, neem contact op met administrator'}, 500
        
        try:
            aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        oude_dimensie_object = self.single_object_by_uuid(uuid)

        if not oude_dimensie_object:
            return {'message': f"Object met identifier {uuid} is niet gevonden"}, 404

        # Voeg de twee objecten samen
        dimensie_object = {**oude_dimensie_object, **aanpassingen}
        
        values = [dimensie_object[k] for k in self.update_fields]
        
        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(self.update_query, *values)
                new_uuid = cursor.fetchone()[0]
            except pyodbc.IntegrityError as e:
                pattern = re.compile(r'FK_\w+_(\w+)')
                match = pattern.search(e.args[-1]).group(1)
                if match:
                    return {'message': f'Database integriteitsfout, een identifier naar een "{match}" object is niet geldig'}, 404
                else:
                    return {'message': 'Database integriteitsfout'}, 404
            except pyodbc.DatabaseError:
                    return {'message': f'Database fout, neem contact op met de systeembeheerder'}, 500
            connection.commit()
        
        return {"Resultaat_UUID": f"{new_uuid}"}