from flask import Flask, jsonify
from flask_restful import Resource, Api
from datetime import timedelta
from flask_jwt_extended import (
    JWTManager, jwt_required
)
import click

from Dimensies.dimensie import Dimensie, DimensieList, DimensieLineage


from Feiten.feit import FeitenList, Feit, FeitenLineage
from Feiten.beleidsbeslissing import Beleidsbeslissingen_Meta_Schema, Beleidsbeslissingen_Fact_Schema, Beleidsbeslissingen_Read_Schema

from Dimensies.geothemas import Geothema
from Dimensies.gebruikers import Gebruiker
from Dimensies.werkingsgebieden import Werkingsgebied


from Special.verordeningsstructuur import Verordening_Structuur
from Auth.views import login, tokenstat
from Auth.commands import new_client_creds, new_client_creds_gebruikers

from Stats.views import stats

from Search.views import search

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from flask_cors import CORS

from elasticsearch_dsl import connections, Index

import json

from Stats.views import stats

from datamodel import dimensies, feiten

from elasticsearch_dsl import Index, Keyword, Mapping, Nested, TermsFacet, connections, Search
from elasticsearch import Elasticsearch

current_version = '0.1'

# FLASK SETUP

app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = 'ZYhFfDSXvdAgkHXSu4NXtJAV8zoWRo8ki4XBtHffLuf4mx3rVxdev'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_HEADER_TYPE'] = "Token"
api = Api(app, prefix=f'/v{current_version}', decorators=[jwt_required, ])
# api = Api(app, prefix=f'/v{current_version}')
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

# ELASTICSEARCH SETUP

es = Elasticsearch()
connections.create_connection(hosts=['localhost'], timeout=20)
app.add_url_rule(f'/v{current_version}/search', 'search', search, methods=['GET'])


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
# DOCUMENTATIE

# for ept, view_func in app.view_functions.items():
#     if ept in dimension_ept:
#         with app.test_request_context():
#             schema_name = ept.split("_")[0] + "_Schema"
#             schema, slug, tn, ac_tn, sn, pl = list(filter(lambda l: l[0].__name__ == schema_name, dimensie_schemas))[0]
#             # Hacky code die de dynamische docstrings maakt
#             for method_name in view_func.methods:
#                 method_name = method_name.lower()
#                 method = getattr(view_func.view_class, method_name)
#                 method.__doc__ = method.__doc__.format(singular=sn, schema=schema.__name__, plural=pl)
#             spec.path(view=view_func)

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
                 '/verordeningstructuur/<string:verordeningstructuur_uuid>')

# api.add_resource(BeleidsBeslissing, '/beleidsbeslissingen',
#                  '/beleidsbeslissingen/<string:beleidsbeslissing_uuid>')

if __name__ == '__main__':
    app.run()
