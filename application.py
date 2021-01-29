# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import json
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from flask_restful import Api, Resource

import datamodel
import Endpoints.endpoint
from Auth.views import jwt_required_not_GET, login, tokenstat
from Models import gebruikers
from Spec.spec import specView
from Endpoints.search import searchView

current_version = '0.1'

# ENV SETUP
load_dotenv()

# FLASK SETUP
app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=4)
api = Api(app, prefix=f'/v{current_version}',
          decorators=[jwt_required_not_GET, ])
jwt = JWTManager(app)


# JWT CONFIG
@jwt.unauthorized_loader
def custom_unauthorized_loader(reason):
    return jsonify(
        {"message": f"Authorisatie niet geldig: '{reason}'"}), 400


# ROUTING RULES
for schema in datamodel.endpoints:
    api.add_resource(Endpoints.endpoint.Lineage, f'/{schema.Meta.slug}/<int:id>', endpoint=f'{schema.Meta.slug.capitalize()}_Lineage',
                     resource_class_args=(schema,))

    api.add_resource(Endpoints.endpoint.FullList, f'/{schema.Meta.slug}', endpoint=f'{schema.Meta.slug.capitalize()}_List',
                     resource_class_args=(schema,))

    api.add_resource(Endpoints.endpoint.ValidList, f'/valid/{schema.Meta.slug}', endpoint=f'{schema.Meta.slug.capitalize()}_Validlist',
                     resource_class_args=(schema,))

    api.add_resource(Endpoints.endpoint.ValidLineage, f'/valid/{schema.Meta.slug}/<int:id>', endpoint=f'{schema.Meta.slug.capitalize()}_Validlineage',
                     resource_class_args=(schema,))
    
    api.add_resource(Endpoints.endpoint.SingleVersion, f'/version/{schema.Meta.slug}/<string:uuid>', endpoint=f'{schema.Meta.slug.capitalize()}_Version',
                     resource_class_args=(schema,))


app.add_url_rule(f'/v{current_version}/login',
                 'login', login, methods=['POST'])
app.add_url_rule(f'/v{current_version}/tokeninfo',
                 'tokenstat', tokenstat, methods=['GET'])
api.add_resource(gebruikers.Gebruiker, '/gebruikers',
                 '/gebruikers/<string:gebruiker_uuid>')
app.add_url_rule(f'/v{current_version}/spec',
                 'spec', specView, methods=['GET'])
app.add_url_rule(f'/v{current_version}/search',
                 'search', searchView, methods=['GET'])


if __name__ == '__main__':
    app.run()
