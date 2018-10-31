from flask_restful import Resource
import records
import pyodbc
from flask import request
import marshmallow as MM
from operator import eq
from globals import db_connection_string, db_connection_settings
import marshmallow as MM
# from .dimensie import Dimensie


class Dimensie_Schema(MM.Schema):
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
    """Een algemene dimensie met endpoints
    Assumpties:
        - General fields zijn aanwezig
        - Kind van Ambitie_Schema
    Ideeën:
        - Subclass general_dimensie_schema
    """
    _identifier_field = 'UUID'

    _general_fields = ['Begin_Geldigheid',
                       'Eind_Geldigheid',
                       'Created_By',
                       'Created_Date',
                       'Modified_By',
                       'Modified_Date']

    def __init__(self, tableschema, tablename_all, tablename_actueel=None):
        self._tablename_all = tablename_all

        if tablename_actueel:
            self._tablename_actueel = tablename_actueel
        else:
            self._tablename_actueel = tablename_all

        self._tableschema = tableschema
        self.uuid_query = f'SELECT * FROM {tablename_all} WHERE UUID=:uuid'
        self.all_query = f'SELECT * FROM {tablename_actueel}'
        self.post_fields = list(filter(lambda f: not(eq(f, "UUID")),
                                       tableschema().fields.keys()))

        post_fields_list = ', '.join(self.post_fields)
        parameter_marks = ', '.join(['?' for _ in self.post_fields])

        print(post_fields_list)

        self.create_query = f'''INSERT INTO {tablename_all}
            ({post_fields_list})
            OUTPUT inserted.UUID
            VALUES ({parameter_marks})'''
        print(self.create_query)

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
        GET endpoint voor deze dimensie
        """
        if uuid:
            dimensie_object = self.single_object_by_uuid(uuid)

            if not dimensie_object:
                return {'message': f"Object met identifier {uuid} is niet gevonden in table {self._tablename_all}"}, 404

            schema = self._tableschema()
            return(schema.dump(dimensie_object))
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
                exclude=('UUID', 'Modified_By', 'Modified_Date'),
                unknown=MM.utils.RAISE)

        except ValueError:
            return {'message': 'Server fout in endpoint, neem contact op met administrator'}, 500

        try:
            dim_object = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        # Modified equals created on creation
        dim_object['Modified_By'] = dim_object['Created_By']
        dim_object['Modified_Date'] = dim_object['Created_Date']

        values = [dim_object[k] for k in self.post_fields]

        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(self.create_query, *values)
        new_uuid = cursor.fetchone()[0]

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
                exclude = ('UUID', 'Created_By', 'Created_Date'),
                partial=('Titel', 'Omschrijving', 'Weblink', 'Begin_Geldigheid', 'Eind_Geldigheid'),
                unknown=MM.utils.RAISE)
        except ValueError:
            return {'message': 'Server fout in endpoint, neem contact op met administrator'}, 500
        try:
            aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        oude_dimensie_object = dimensie_object = self.single_object_by_uuid(uuid)

        if not oude_ambitie_object:
            return {'message': f"Object met identifier {uuid} is niet gevonden in table {self._tablename_all}"}, 404

        dimensie_object = {**oude_dimensie_object, **aanpassingen}

        return {"Resultaat_UUID": f"{ambitie_uuid}"}
