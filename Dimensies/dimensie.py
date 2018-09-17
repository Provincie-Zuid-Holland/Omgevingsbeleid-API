from flask_restful import Resource
import records
import pyodbc
from flask import request
import marshmallow as MM
from operator import eq
from globals import db_connection_string, db_connection_settings


class Dimensie(Resource):
    """Een algemene dimensie
    Assumpties:
        - General fields zijn aanwezig
        - [UUID, specific_fields, Created_By, Begin_Geldigheid,
            Eind_Geldigheid, Created_Date, Modified_By, Modified_Data]
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
        self.non_id_fields = list(filter(lambda f: not(eq(f, "UUID")),
                                         tableschema().fields.keys()))

        self.non_id_fields_query = ', '.join(self.non_id_fields)
        parameter_marks = ', '.join(['?' for _ in self.non_id_fields])

        self.create_query = f'''INSERT INTO {tablename_all}
            ({self.non_id_fields_query})
            OUTPUT inserted.UUID
            VALUES ({parameter_marks})'''

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

        # Specific fields are all fields that are not required for every dimension
        specific_fields = [
            dim_object[f] for f in schema.fields if f not in self._general_fields]

        # Modified equals created on creation
        dim_object['Modified_By'] = dim_object['Created_By']
        dim_object['Modified_Date'] = dim_object['Created_Date']

        general_fields = [
            dim_object[f] for f in self._general_fields
        ]

        values = specific_fields + general_fields

        connection = pyodbc.connect(db_connection_settings)
        cursor = connection.cursor()
        cursor.execute(self.create_query, *values)
        new_uuid = cursor.fetchone()[0]

        connection.commit()
        return {"Resultaat_UUID": f"{new_uuid}"}

    # def patch(self, ambitie_uuid=None):
    #     if not ambitie_uuid:
    #         return {'message': "Methode PATCH alleen geldig op een enkel object, voeg een identifier toe aan de URL"}, 400

    #     patch_schema = Ambitie_Schema(
    #         partial=('Titel', 'Omschrijving', 'Weblink', 'Begin_Geldigheid', 'Eind_Geldigheid'),
    #         exclude = ('UUID', 'Created_By', 'Created_Date'),
    #         unknown=MM.utils.RAISE
    #         )
    #     try:
    #         ambitie_aanpassingen = patch_schema.load(request.get_json())
    #     except MM.exceptions.ValidationError as err:
    #         return err.normalized_messages(), 400

    #     oude_ambitie = single_object_by_uuid('Ambities', ambitie_op_uuid, uuid=ambitie_uuid)

    #     if not oude_ambitie:
    #         return {'message': f"Ambitie met UUID {ambitie_uuid} is niet gevonden"}, 404

    #     ambitie = {**oude_ambitie, **ambitie_aanpassingen}

    #     connection = pyodbc.connect(db_connection_settings)
    #     cursor = connection.cursor()
    #     cursor.execute(ambitie_aanpassen,
    #     ambitie['ID'],
    #     ambitie['Titel'],
    #     ambitie['Omschrijving'],
    #     ambitie['Weblink'],
    #     ambitie['Begin_Geldigheid'],
    #     ambitie['Eind_Geldigheid'],
    #     ambitie['Created_By'],
    #     ambitie['Created_Date'],
    #     ambitie['Modified_By'],
    #     ambitie['Modified_Date'])
    #     ambitie_uuid = cursor.fetchone()[0]

    #     connection.commit()
    #     return {"Resultaat_UUID": f"{ambitie_uuid}"}
