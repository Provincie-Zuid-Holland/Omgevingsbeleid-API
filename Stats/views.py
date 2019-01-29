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
            result[table] = {}
            # Aantal objecten
            query = f"SELECT COUNT(DISTINCT(ID)), COUNT(*) from {table} WHERE UUID != '00000000-0000-0000-0000-000000000000'"
            results = db.query(query)
            result[table]['Aantal objecten'] = results.first()[0]
            result[table]['Aantal rows'] = results.first()[1]
            # Laatste modificatie
            query = f"SELECT TOP 1 UUID, Modified_Date from {table} ORDER BY Modified_Date DESC"
            results = db.query(query)
            first = results.first()
            result[table]['Laatste modificatie'] = {'UUID': first[0], 'Modified_Date': first[1].isoformat(sep=' ')}
        query = f"SELECT COUNT(*) FROM Gebruikers WHERE UUID != '00000000-0000-0000-0000-000000000000'"
        results = db.query(query)
        result['Gebruikers'] = {}
        result['Gebruikers']['Aantal objecten'] = results.first()[0]   

    return jsonify(result)