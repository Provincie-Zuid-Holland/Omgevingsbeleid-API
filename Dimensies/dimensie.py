from flask_restful import Resource
import records
import pyodbc
from flask import request, jsonify
import marshmallow as MM
from operator import eq
from globals import db_connection_string, db_connection_settings
import re
import datetime
from flask_jwt_extended import get_jwt_identity
from elasticsearch_dsl import Document, Integer, Text
# from .dimensie import Dimensie


class Dimensie_Schema(MM.Schema):
    """
    Schema voor de standaard velden van een dimensie
    """
    ID = MM.fields.Integer(search_field="Keyword")
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


def attribute_or_str(mmfield):
    """
    This functions takes an Marsmallow Field object and returns it's name as String if the field has no 'attribute' value.
    If it does have an attribute value, it returns the attribute value
    """
    if mmfield[1].attribute:
        return mmfield[1].attribute
    else:
        return mmfield[0]


class DimensieLineage(Resource):

    # Velden die niet in een PATCH request gestuurd mogen worden
    _excluded_patch_fields = ['ID', 'UUID', 'Created_By', 'Created_Date', 'Modified_Date', 'Modified_By']
    _general_fields = ['ID',
                       'UUID',
                       'Begin_Geldigheid',
                       'Eind_Geldigheid',
                       'Created_By',
                       'Created_Date',
                       'Modified_By',
                       'Modified_Date']

    def __init__(self, tableschema, tablename_all):
        self.lineage_query = f'''SELECT * FROM {tablename_all} WHERE ID = :id ORDER BY Modified_Date DESC'''
        self._tableschema = tableschema
        # Is het gegeven schema een superset van Dimensie_Schema?
        required_fields = Dimensie_Schema().fields.keys()
        schema_fields = tableschema().fields
        assert all([field in schema_fields for field in required_fields]), "Gegeven schema is geen superset van Dimensie Schema"

        self.lineage_last_query = f'''SELECT TOP(1) * FROM {tablename_all} WHERE ID = :id ORDER BY Modified_Date DESC'''

        # Partial velden voor de PATCH
        self._partial_patch_fields = [field for field in schema_fields if field not in self._general_fields]
        # convert all fields to the correct naming
        self.patch_query_fields = list(filter(lambda field: field != "UUID", map(attribute_or_str, schema_fields.items())))

        update_fields_list = ', '.join(self.patch_query_fields)
        update_parameter_marks = ', '.join(['?' for _ in self.patch_query_fields])

        self.update_query = f'''INSERT INTO {tablename_all} ({update_fields_list}) OUTPUT inserted.UUID VALUES ({update_parameter_marks})'''

        self.uuid_query = f'SELECT * FROM {tablename_all} WHERE UUID=:uuid'

    def get(self, id):
        """
        GET endpoint voor {plural} lineages.
        ---
        description: Verkrijg een de lineage lijst van een {singular} object
        responses:
            200:
                description: Succesvolle request
                content:
                    application/json:
                        schema:
                            type: array
                            items: {schema}
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
        db = records.Database(db_connection_string)
        dimensie_objecten = db.query(self.lineage_query, id=id)
        if not(any(dimensie_objecten)):
            return {'message': f'Object met ID={id} niet gevonden'}, 404
        schema = self._tableschema()
        return(schema.dump(dimensie_objecten, many=True))

    def patch(self, id):
        """
        PATCH endpoint voor deze dimensie.
        ---
        description: Wijzig een {singular} op basis van ID
        parameters:
            - in: path
              name:id
              description: De UUID van het te wijzigen object
              schema:
                type: string
                format: uuid
        responses:
            200:
                description: {singular} is succesvol gewijzigd
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
        request_time = datetime.datetime.now()
        try:
            patch_schema = self._tableschema(
                exclude=self._excluded_patch_fields,
                partial=self._partial_patch_fields,
                unknown=MM.utils.RAISE)

        except ValueError:
            return {'message': 'Server fout in endpoint, neem contact op met administrator'}, 500

        try:
            aanpassingen = patch_schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        db = records.Database(db_connection_string)
        dimensie_objecten = db.query(self.lineage_last_query, id=id)
        if not(any(dimensie_objecten)):
            return {'message': f'Object met ID={id} niet gevonden'}, 404
        if len(dimensie_objecten) != 1:
            return {'message': 'Server fout in endpoint, neem contact op met administrator'}, 500
        oude_object = dimensie_objecten[0]

        dimensie_object = {**oude_object, **aanpassingen}  # Dict merging using kwargs method

        dimensie_object.pop('UUID')
        dimensie_object['Modified_Date'] = request_time
        dimensie_object['Modified_By'] = get_jwt_identity()['UUID']

        values = [dimensie_object[k] for k in self.patch_query_fields]
        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(self.update_query, *values)
            except pyodbc.IntegrityError as e:
                pattern = re.compile(r'FK_\w+_(\w+)')
                match = pattern.search(e.args[-1]).group(1)
                if match:
                    return {'message': f'Database integriteitsfout, een identifier naar een "{match}" object is niet geldig'}, 404
                else:
                    return {'message': 'Database integriteitsfout'}, 404
            except pyodbc.DatabaseError as e:
                return {'message': f'Database fout, neem contact op met de systeembeheerder Exception:[{e}]'}, 500
            new_uuid = cursor.fetchone()[0]
            connection.commit()

        db = records.Database(db_connection_string)
        result = db.query(self.uuid_query, uuid=new_uuid).first()
        dump_schema = self._tableschema()

        return dump_schema.dump(result), 200


class DimensieList(Resource):
    # Velden die niet in een POST request gestuurd mogen worden
    _excluded_post_fields = ['ID', 'UUID', 'Modified_By', 'Modified_Date', 'Created_Date', 'Created_By']

    # Veld dat dient als identificatie
    _identifier_fields = ['UUID', 'ID']

    def __init__(self, tableschema, tablename_all, tablename_actueel, search_model=None):
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
            if fieldkey in self._identifier_fields:
                continue
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

        self.uuid_query = f'SELECT * FROM {tablename_all} WHERE UUID=:uuid'
        self.search_model = search_model
        if self.search_model:
            self.search_model.init()

    def get(self):
        """
        GET endpoint voor {plural}.
        ---
        description: Verkrijg een lijst van alle fungerende {plural}
        responses:
            200:
                description: Succesvolle request
                content:
                    application/json:
                        schema:
                            type: array
                            items: {schema}
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
        query = self.all_query
        filter_values = None
        filters = request.args
        if filters:
            invalids = [f for f in filters if f not in self.query_fields]
            if invalids:
                return {'message': f"Filter(s) '{' '.join(invalids)}' niet geldig voor dit type object. Geldige filters: '{', '.join(self.query_fields)}''"}, 403
            conditionals = [f"{f} = ?" for f in filters]
            conditional = " WHERE " + " AND ".join(conditionals)
            filter_values = [filters[f] for f in filters]
            query = query + conditional
        
        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            try:
                if filter_values:
                    cursor.execute(query, *filter_values)
                else:
                    cursor.execute(query)
            except pyodbc.DatabaseError as e:
                return {'message': f'Database fout, neem contact op met de systeembeheerder Exception:[{e}]'}, 500
            dimensie_objecten = cursor.fetchall()
            # dimensie_objecten = objects_from_query(query)
            schema = self._tableschema()
            return(schema.dump(dimensie_objecten, many=True))

    def post(self):
        """
        POST endpoint voor {plural}.
        ---
        description: Creeër een nieuwe {singular}
        responses:
            200:
                description: {singular} succesvol aangemaakt
                content:
                    application/json:
                        schema: {schema}
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
            return {'message': 'Server fout in endpoint, neem contact op met de administrator'}, 500

        if request.get_json() is None:
            return {'message': 'Request data empty'}, 400

        try:
            dim_object = schema.load(request.get_json())
        except MM.exceptions.ValidationError as err:
            return err.normalized_messages(), 400

        # Add missing information
        dim_object['Created_By'] = get_jwt_identity()['UUID']
        dim_object['Created_Date'] = datetime.datetime.now()
        dim_object['Modified_Date'] = dim_object['Created_Date']
        dim_object['Modified_By'] = dim_object['Created_By']

        # return dump_schema.dump(dim_object), 200

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

        db = records.Database(db_connection_string)
        result = db.query(self.uuid_query, uuid=new_uuid).first()
        dump_schema = self._tableschema()
        result = dump_schema.dump(result)
        return result, 201


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

        # Bouw hier de queries op
        self._tableschema = tableschema
        self.uuid_query = f'SELECT * FROM {tablename_all} WHERE UUID=:uuid'
        self.all_query = f'SELECT * FROM {tablename_actueel}'

        self.query_fields = list(filter(lambda fieldname: not(eq(fieldname, self._identifier_field)), schema_fields))

        # PATCH Queries are build using this list (preserving order)
        self.update_fields = self.query_fields

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
        GET endpoint voor {plural}.
        ---
        description: Verkrijg een {singular} op basis van UUID
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
                        schema: {schema}
            404:
                description: {singular} met dit UUID niet gevonden
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
