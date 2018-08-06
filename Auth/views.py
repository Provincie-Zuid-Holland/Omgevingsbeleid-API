from flask import Flask, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity
)
from passlib.hash import bcrypt
from globals import db_connection_string, db_connection_settings
import pyodbc


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
    connection = pyodbc.connect(db_connection_settings)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Clients WHERE identifier = ?", identifier)
    passwordhash = cursor.fetchone()[1]
    if passwordhash:
        if bcrypt.verify(password, passwordhash):
            access_token = create_access_token(identity=identifier)
            return jsonify(access_token=access_token), 200    
    return jsonify(
        {"message": "Wachtwoord of gebruikersnaam ongeldig"}), 401
    
