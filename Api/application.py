# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

from flask import Flask
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

from Api.settings import ProdConfig
from Api.database import db
from Api.api import api as rest_api


cors = CORS()
jwt = JWTManager()


def create_app(config_object=ProdConfig):
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_extensions(app)
    register_api(app)
    register_shellcontext(app)
    register_commands(app)

    return app


def register_extensions(app):
    cors.init_app(app)
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)
    rest_api.init(app)


# JWT CONFIG
@jwt.unauthorized_loader
def custom_unauthorized_loader(reason):
    return jsonify({"message": f"Authorisatie niet geldig: '{reason}'"}), 401
