import marshmallow as MM
from flask_restful import Resource
from flask import request, jsonify
import datetime
from flask_jwt_extended import get_jwt_identity
import pyodbc
from globals import db_connection_string, db_connection_settings, min_datetime, max_datetime, row_to_dict
import json
import datetime

class Kimball_Manager:
    def __init__(self, linked_table):
        self.linked_table = linked_table
    
    def retrieve(self, connection, UUID=None):
        cur = connection.cursor()
        query = f"SELECT * FROM {self.linked_table}"
        return map(row_to_dict, cur.execute(query).fetchall())
    
    def store(self):
        pass

    def _flatten_rows(self, rows):
        """
        Flatten a collection of rows, using UUID as the main key.
        Expects a [field]_omschrijving for all columns named fk_[field] in the table. 
        """
        # Use a dict to keep a reference to the processed objects
        results = {} 
        for row in rows:
            result = {}
            for field in row:
                if field.startswith('fk_'):
                    field_name = field[2:]
                    if field_name in result:
                        result[field_name].append(row[field])
                    else:
                        result[field_name] = { 'UUID': row[field]]
                if field.endswith('_omschrijving'):
        # TODO: Fix this.

        results[row['UUID']] = row

class FeitenList(Resource):

    def __init__(self, read_schema, write_schema, manager):
        """
        Read_schema will be used for reading (Database -> Json)
        Write_schema will be user for writing (JSON -> Database)
        """
        self.read_schema = read_schema()
        self.write_schema = write_schema()
        self.manager = manager(read_schema, write_schema, self.read_schema.Meta.source_table)

    def get(self):
        """
        Retrieves a list of alle objects that are currently valid
        """
        with pyodbc.connect(db_connection_settings, autocommit=False) as connection: 
            try:
                # Retrieve all objects from the database
                facts = self.manager.retrieve(connection)
                print(facts)
            except pyodbc.Error as odbc_ex:
                code = odbc_ex.args[0]
                return {"message": f"Database error [{code}] during handling of request", "detailed": str(odbc_ex)}, 400
            
            try:
                # Read all the objects with the schema to enforce validation
                checked_facts = self.read_schema.load(facts, many=True)
            except MM.exceptions.ValidationError as err:
                return f"Validation error on read, please contact sysadmin. Details: {err.normalized_messages()}", 400
            
            return self.read_schema.dump(checked_facts, many=True)
