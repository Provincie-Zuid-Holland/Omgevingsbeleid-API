# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from Api.settings import ProdConfig
from Api.database import db
from Api.api import create_api
from Api import commands


cors = CORS()
jwt = JWTManager()


def create_app(config_object=ProdConfig):
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_extensions(app)
    rest_api = register_api(app)

    # register_shellcontext(app)
    register_commands(app)

    return app


def register_api(app):
    rest_api = create_api(app)
    rest_api.init_app(app)

    return rest_api


def register_extensions(app):
    cors.init_app(app)
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)

    app.db = db


def register_commands(app):
    app.cli.add_command(commands.setup_views)
    app.cli.add_command(commands.dm_markdown)
    app.cli.add_command(commands.dm_dbdiagram)
    app.cli.add_command(commands.database_test_nills)
    app.cli.add_command(commands.database_test_search_index)

    if not app.config.get("PROD"):
        from Tests.TestUtils.commands import load_fixtures, add_user # noqa
        app.cli.add_command(load_fixtures)
        app.cli.add_command(add_user)


# JWT CONFIG
@jwt.unauthorized_loader
def custom_unauthorized_loader(reason):
    return jsonify({"message": f"Authorisatie niet geldig: '{reason}'"}), 401
