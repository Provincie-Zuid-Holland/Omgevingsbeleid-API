from flask import Flask, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    decode_token,
    get_jwt_identity,
    jwt_required,
    get_raw_jwt
)
from passlib.hash import bcrypt
from globals import db_connection_string, db_connection_settings
import pyodbc
import time
import records



def login():
    if not request.json:
        return jsonify(
            {"message": "Identifier en password parameter niet gevonden"}), 400

    identifier = request.json.get('identifier', None)
    password = request.json.get('password', None)
    if not identifier:
        return jsonify({"message": "Identifier parameter niet gevonden"}), 400
    if not password:
        return jsonify({"message": "Password parameter niet gevonden"}), 400

    # Find identifier
    # connection = pyodbc.connect(db_connection_settings)
    # cursor = connection.cursor()
    # cursor.execute("SELECT * FROM Gebruikers WHERE Gebruikersnaam = ?", identifier)
    db = records.Database(db_connection_string)
    row = db.query("""SELECT UUID, Gebruikersnaam, Email, Rol, Wachtwoord FROM Gebruikers WHERE Email = :gebruikersnaam""", gebruikersnaam=identifier)
    result = row.first()
    if result:
        passwordhash = result['Wachtwoord']
        if passwordhash:
            if bcrypt.verify(password, passwordhash):
                identity_result = dict(result)
                identity_result.pop('Wachtwoord')
                access_token = create_access_token(identity=identity_result)
                raw_token = decode_token(access_token)
                return jsonify({'access_token':access_token, 
                                'expires':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.localtime(raw_token['exp'])),
                                'identifier':raw_token['identity']}), 200    
    return jsonify(
        {"message": "Wachtwoord of gebruikersnaam ongeldig"}), 401
    
@jwt_required
def tokenstat():
    raw_jwt = get_raw_jwt()
    return jsonify({
    'identifier': get_jwt_identity(), 
    'expires':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.localtime(raw_jwt['exp']))
    })
    