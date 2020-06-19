from flask import Flask, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    decode_token,
    get_jwt_identity,
    jwt_required,
    get_raw_jwt,
    verify_jwt_in_request
)
from jwt.algorithms import get_default_algorithms
from passlib.hash import bcrypt
from globals import db_connection_string, db_connection_settings
import pyodbc
import time
import records
import os
from functools import wraps
import jwt

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
                                'identifier':raw_token['identity'],
                                'deployment type':os.getenv('API_ENV')}), 200    
    return jsonify(
        {"message": "Wachtwoord of gebruikersnaam ongeldig"}), 401
    
@jwt_required
def tokenstat():
    raw_jwt = get_raw_jwt()
    return jsonify({
    'identifier': get_jwt_identity(), 
    'expires':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.localtime(raw_jwt['exp']))
    })

def jwt_required_not_GET(fn):
    """
    Only requires a JWT on a non GET request
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method != 'GET':
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        else:
            public_key = """ -----BEGIN PUBLIC KEY-----
            MIIDBTCCAe2gAwIBAgIQWHw7h/Ysh6hPcXpnrJ0N8DANBgkqhkiG9w0BAQsFADAtMSswKQYDVQQDEyJhY2NvdW50cy5hY2Nlc3Njb250cm9sLndpbmRvd3MubmV0MB4XDTIwMDQyNzAwMDAwMFoXDTI1MDQyNzAwMDAwMFowLTErMCkGA1UEAxMiYWNjb3VudHMuYWNjZXNzY29udHJvbC53aW5kb3dzLm5ldDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALhz3sIYOFgt3i1T5BBZY+0Q7WimFlwiORviz1c7DCjriLu6kEG3srSAOj+h0/f4iEbfMzUL7sOD/b2zY4FAqSOr32RrI5N17glaAf2wCIb7gXEIfXjx9shMEua3kfjaxtT7Ks6G52WbooCgqA5rjm/1A8dQ4lcjQmzAZRBu1M00MC3+TT+h2kR8dNu1ESXmbzwFmO84x5UjriqEv3dclL3mgRSIGaj1iwoOOHJOIL4pOOR7DVVk/c2H0++Hb1EkqzEkfkhxU+x8tV421V6RyRzTQF6T6BqFl07nNAcTLAeHKo3yaqH7RRjhuMd9rxM2pAKyz8QCsBr5L7tI06AMr0kCAwEAAaMhMB8wHQYDVR0OBBYEFOI7M+DDFMlP7Ac3aomPnWo1QL1SMA0GCSqGSIb3DQEBCwUAA4IBAQBv+8rBiDY8sZDBoUDYwFQM74QjqCmgNQfv5B0Vjwg20HinERjQeH24uAWzyhWN9++FmeY4zcRXDY5UNmB0nJz7UGlprA9s7voQ0Lkyiud0DO072RPBg38LmmrqoBsLb3MB9MZ2CGBaHftUHfpdTvrgmXSP0IJn7mCUq27g+hFk7n/MLbN1k8JswEODIgdMRvGqN+mnrPKkviWmcVAZccsWfcmS1pKwXqICTKzd6WmVdz+cL7ZSd9I2X0pY4oRwauoE2bS95vrXljCYgLArI3XB2QcnglDDBRYu3Z3aIJb26PTIyhkVKT7xaXhXl4OgrbmQon9/O61G2dzpjzzBPqNP
            -----END PUBLIC KEY-----"""
            payload = jwt.decode(request.headers['Authorization'].split(" ")[1], key=public_key, algorithms='RS256', audience=["9f8b79f1-4fd7-4fa0-9f51-6077e8317b8d"])
            print(payload)
            return fn(*args, **kwargs)
    return wrapper
