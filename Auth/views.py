# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from flask import Flask, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    decode_token,
    get_jwt_identity,
    jwt_required,
    get_raw_jwt,
    verify_jwt_in_request
)
from passlib.hash import bcrypt
from globals import db_connection_settings, row_to_dict
import pyodbc
import time
import os
from functools import wraps

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
    with pyodbc.connect(db_connection_settings) as connection:
        cursor = connection.cursor()
        query = """SELECT UUID, Gebruikersnaam, Email, Rol, Wachtwoord FROM Gebruikers WHERE Email = ?"""
        cursor.execute(query, identifier)
        result = cursor.fetchone()
    
    if result:
        result = row_to_dict(result)
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
            return fn(*args, **kwargs)
    return wrapper
