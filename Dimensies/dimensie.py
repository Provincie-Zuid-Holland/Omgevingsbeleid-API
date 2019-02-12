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
    Created_By = MM.fields.Str(required=True)
    Created_Date = MM.fields.DateTime(format='iso', required=True)
    Modified_By = MM.fields.Str(required=True)
    Modified_Date = MM.fields.DateTime(format='iso', required=True)
    
    class Meta:
        ordered = True


class Dimensie(Resource):
    """
    Een dimensie met bijbehorend lees/schrijf gedrag.
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

    # Velden die niet in een POST request gestuurd mogen worden
    _excluded_post_fields = ['UUID', 'Modified_By', 'Modified_Date']

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
        
        # POST Queries are build using this list (preserving order) 
        self.query_fields = list(filter(lambda fieldname: not(eq(fieldname, self._identifier_field)), schema_fields))

        # PATCH Queries are build using this list (preserving order)
        self.update_fields = self.query_fields + ['ID']
        
        update_fields_list = ', '.join(self.update_fields)
        update_parameter_marks = ', '.join(['?' for _ in self.update_fields])

        create_fields_list = ', '.join(self.query_fields)
        create_parameter_marks = ', '.join(['?' for _ in self.query_fields])

        self.create_query = f'''INSERT INTO {tablename_all}
            ({create_fields_list})
            OUTPUT inserted.UUID
            VALUES ({create_parameter_marks})'''

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

    def objects_from_query(self):
        """
        Verkrijg alle objecten uit een table
        """
        db = records.Database(db_connection_string)
        return db.query(self.all_query)

    def get(self, uuid=None):
        """
        GET endpoint voor deze dimensie.
        ---
        description: Verkrijg een object op basis van UUID
        responses:
            200:
                content:
                    application/json:
                        schema: Ambitie_Schema
            404:
                content:
                    application/json:
                        schema: Ambitie_Schema
        """
        # Een enkel object verkrijgen
        if uuid:
            dimensie_object = self.single_object_by_uuid(uuid)

            if not dimensie_object:
                return {'message': f"Object met identifier {uuid} is niet gevonden in table {self._tablename_all}"}, 404

            schema = self._tableschema()
            return(schema.dump(dimensie_object))
        # Alle objecten verkrijgen
        else:
            dimensie_objecten = self.objects_from_query()
            schema = self._tableschema()
            return(schema.dump(dimensie_objecten, many=True))

    def post(self, uuid=None):
        """
        POST endpoint voor deze dimensie
        """
        if uuid:
            return {'message': 'Methode POST niet geldig op een enkel object, verwijder identifier uit URL'}, 400
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

        # Modification data is the same as creation data (because we just created this object)
        dim_object['Modified_By'] = dim_object['Created_By']
        dim_object['Modified_Date'] = dim_object['Created_Date']

        values = [dim_object[k] for k in self.query_fields]
        
        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(self.create_query, *values)
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

    def patch(self, uuid=None):
        """
        PATCH endpoint voor deze dimensie
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