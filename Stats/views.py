from flask import Flask, jsonify, request
from globals import db_connection_string, db_connection_settings
import pyodbc
import records


def stats():
    tables = [
    'Maatregelen',
    'Opgaven',
    'Beleidsbeslissingen',
    'Ambities',
    'BeleidsRegels',
    'Verordeningen',
    'BeleidsRelaties',
    'Doelen',
    'ProvincialeBelangen', 
    'Themas',
    'Omgevingsbeleid',
    'WerkingsGebieden',
    'GeoThemas']
    
    result = {}
    with records.Database(db_connection_string) as db:
        for table in tables:
            query = f"SELECT COUNT(DISTINCT(ID)) from {table} WHERE UUID != '00000000-0000-0000-0000-000000000000'"
            results = db.query(query)
            result[table] = {}
            result[table]['Aantal objecten'] = results.first()[0]
            query = f"SELECT COUNT(*) from {table} WHERE UUID != '00000000-0000-0000-0000-000000000000'"
            results = db.query(query)
            result[table]['Aantal rows'] = results.first()[0]
    return jsonify(result)