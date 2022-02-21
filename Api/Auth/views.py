# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from flask import Flask, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    decode_token,
    get_jwt_identity,
    jwt_required,
    get_raw_jwt,
    verify_jwt_in_request,
)
from passlib.hash import bcrypt
import pyodbc
import time
import os
from functools import wraps
from password_strength import PasswordPolicy
from flask import current_app

from Api.Utils import row_to_dict

policy = PasswordPolicy.from_names(
    length=12,
    uppercase=1,
    numbers=1,
    special=1,
)


def printTest(test):
    name = type(test).__name__.lower()
    count = test.args[0]
    if name == "length":
        return f"minimaal {count} karakters bevatten"
    if name == "uppercase":
        if count > 1:
            return f"minimaal {count} hoofdletters bevatten"
        else:
            return f"minimaal {count} hoofdletter bevatten"
    if name == "numbers":
        if count > 1:
            return f"minimaal {count} nummers bevatten"
        else:
            return f"minimaal {count} nummer bevatten"

    if name == "special":
        if count > 1:
            return f"minimaal {count} speciale karakters bevatten"
        else:
            return f"minimaal {count} speciaal karakter bevatten"


def login():
    if not request.json:
        return (
            jsonify({"message": "Identifier en password parameter niet gevonden"}),
            400,
        )

    identifier = request.json.get("identifier", None)
    password = request.json.get("password", None)
    if not identifier:
        return jsonify({"message": "Identifier parameter niet gevonden"}), 400
    if not password:
        return jsonify({"message": "Password parameter niet gevonden"}), 400

    # Find identifier
    with pyodbc.connect(current_app.config['DB_CONNECTION_SETTINGS']) as connection:
        cursor = connection.cursor()
        query = """SELECT UUID, Gebruikersnaam, Email, Rol, Wachtwoord FROM Gebruikers WHERE Email = ?"""
        cursor.execute(query, identifier)
        result = cursor.fetchone()

    if result:
        result = row_to_dict(result)
        passwordhash = result["Wachtwoord"]
        if passwordhash:
            if bcrypt.verify(password, passwordhash):
                identity_result = dict(result)
                identity_result.pop("Wachtwoord")
                access_token = create_access_token(identity=identity_result)
                raw_token = decode_token(access_token)
                return (
                    jsonify(
                        {
                            "access_token": access_token,
                            "expires": time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ", time.localtime(raw_token["exp"])
                            ),
                            "identifier": raw_token["identity"],
                            "deployment type": os.getenv("API_ENV"),
                        }
                    ),
                    200,
                )
    return jsonify({"message": "Wachtwoord of gebruikersnaam ongeldig"}), 401


@jwt_required
def password_reset():
    password = request.json.get("password", None)
    new_password = request.json.get("new_password", None)
    if not password:
        return jsonify({"message": "password parameter not found"}), 400
    if not new_password:
        return jsonify({"message": "new_password parameter not found"}), 400
    else:
        if errors := policy.test(new_password):
            return {
                "message": "Password does not meet requirements",
                "errors": list(map(printTest, errors)),
            }, 400

        with pyodbc.connect(current_app.config['DB_CONNECTION_SETTINGS']) as connection:
            cursor = connection.cursor()
            query = """SELECT UUID, Wachtwoord FROM Gebruikers WHERE UUID = ?"""
            cursor.execute(query, get_jwt_identity()["UUID"])
            result = cursor.fetchone()

        if not result:
            return {"message": "Unable to find user"}, 401

        if bcrypt.verify(password, result[1]):
            hash = bcrypt.hash(new_password)
            with pyodbc.connect(current_app.config['DB_CONNECTION_SETTINGS']) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """UPDATE Gebruikers SET Wachtwoord = ? WHERE UUID = ?""",
                    hash,
                    get_jwt_identity()["UUID"],
                )
                return {"message": "Password changed"}, 200

        else:
            return {"message": "Password invalid"}, 401


@jwt_required
def tokenstat():
    raw_jwt = get_raw_jwt()
    return jsonify(
        {
            "identifier": get_jwt_identity(),
            "expires": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.localtime(raw_jwt["exp"])
            ),
        }
    )
