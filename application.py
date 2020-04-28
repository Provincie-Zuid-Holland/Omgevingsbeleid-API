import json
import os
from datetime import timedelta

import click
from flask import Flask, jsonify

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from Auth.commands import new_client_creds, new_client_creds_gebruikers
from Auth.views import login, tokenstat, jwt_required_not_GET
from datamodel import dimensies, feiten
from Dimensies.dimensie import Dimensie, DimensieLineage, DimensieList
from Dimensies.gebruikers import Gebruiker
from Dimensies.geothemas import Geothema
from Dimensies.werkingsgebieden import Werkingsgebied
from elasticsearch import Elasticsearch
from elasticsearch_dsl import (Index, Keyword, Mapping, Nested, Search,
                               TermsFacet, connections)
from Feiten.beleidsbeslissing import (Beleidsbeslissingen_Read_Schema)
from Feiten.feit import Feit, FeitenLineage, FeitenList
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from flask_restful import Api, Resource
from Search.views import search, geo_search
from Special.verordeningsstructuur import Verordening_Structuur
from Stats.views import stats

current_version = '0.1'

# FLASK SETUP

app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=4)
app.config['JWT_HEADER_TYPE'] = "Token"
api = Api(app, prefix=f'/v{current_version}', decorators=[jwt_required_not_GET, ])
jwt = JWTManager(app)


# APISPEC SETUP

spec = APISpec(
    title='Omgevingsbeleid service',
    version=current_version,
    openapi_version='3.0.2',
    plugins=[
        MarshmallowPlugin(),
        FlaskPlugin()
    ]
)



app.add_url_rule(f'/v{current_version}/search', 'search', search, methods=['GET'])
app.add_url_rule(f'/v{current_version}/search/geo', 'geo-search', geo_search, methods=['GET'])


# JWT CONFIG
@jwt.unauthorized_loader
def custom_unauthorized_loader(reason):
    return jsonify(
        {"message": f"Authorisatie niet geldig: '{reason}'"}), 400


# CUSTOM COMMANDS

@app.cli.command()
@click.argument('client_identifier')
def generate_client_creds(client_identifier):
    result = new_client_creds(client_identifier)
    click.echo(result)
    click.pause()


@app.cli.command()
def generate_passwords():
    result = new_client_creds_gebruikers()
    for gebruikersnaam, credentials in result:
        click.echo(f"{gebruikersnaam}\t\t{credentials}")
    click.pause()


app.add_url_rule(f'/v{current_version}/login', 'login', login, methods=['POST'])
app.add_url_rule(f'/v{current_version}/stats', 'stats', stats, methods=['GET'])

# ROUTING RULES

dimension_ept = []

for dimensie in dimensies:
    spec.components.schema(dimensie['singular'], schema=dimensie['schema'])
    api.add_resource(Dimensie, f'/{dimensie["slug"]}/version/<string:uuid>', endpoint=dimensie['singular'],
                     resource_class_args=(dimensie['schema'], dimensie['tablename'], dimensie['latest_tablename']))
    dimension_ept.append(dimensie['singular'])
    api.add_resource(DimensieList, f'/{dimensie["slug"]}', endpoint=f"{dimensie['plural']}_lijst",
                     resource_class_args=(dimensie['schema'], dimensie['tablename'], dimensie['latest_tablename']))
    dimension_ept.append(f"{dimensie['plural']}_lijst")
    api.add_resource(DimensieLineage, f'/{dimensie["slug"]}/<int:id>', endpoint=f"{dimensie['plural']}_lineage", resource_class_args=(dimensie['schema'],  dimensie['tablename']))

for feit in feiten:
    general_args = (feit['meta_schema'], feit['meta_tablename'], feit['meta_tablename_actueel'], feit['fact_schema'], feit['fact_tablename'], feit['fact_to_meta_field'], feit['read_schema'])
    api.add_resource(FeitenList, f'/{feit["slug"]}', endpoint=f'{feit["slug"]}_lijst',
                     resource_class_args=general_args)
    api.add_resource(FeitenLineage, f'/{feit["slug"]}/<string:id>', endpoint=f'{feit["slug"]}_lineage',
                     resource_class_args=general_args)
    api.add_resource(Feit, f'/{feit["slug"]}/version/<string:uuid>', endpoint=f'{feit["slug"]}',
                     resource_class_args=general_args)
    spec.components.schema('Beleidsbeslissingen', schema=Beleidsbeslissingen_Read_Schema)

app.add_url_rule(f'/v{current_version}/login',
                 'login', login, methods=['POST'])
app.add_url_rule(f'/v{current_version}/tokeninfo',
                 'tokenstat', tokenstat, methods=['GET'])
app.add_url_rule(f'/v{current_version}/stats',
                 'stats', stats, methods=['GET'])
app.add_url_rule(f'/v{current_version}/spec',
                 'spec', lambda: json.dumps(spec.to_dict(), indent=2), methods=['GET'])

api.add_resource(Werkingsgebied, '/werkingsgebieden',
                 '/werkingsgebieden/<string:werkingsgebied_uuid>')
api.add_resource(Geothema, '/geothemas',
                 '/geothemas/<string:geothema_uuid>')
api.add_resource(Gebruiker, '/gebruikers',
                 '/gebruikers/<string:gebruiker_uuid>')
api.add_resource(Verordening_Structuur, '/verordeningstructuur',
                 '/verordeningstructuur/<int:verordeningstructuur_id>',
                 '/verordeningstructuur/version/<uuid:verordeningstructuur_uuid>')

if __name__ == '__main__':
    app.run()
