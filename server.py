from flask import Flask, jsonify
from flask_restful import Resource, Api
from pprint import pprint
from datetime import timedelta
from flask_jwt_extended import (
    JWTManager, jwt_required
)
import click
from collections import namedtuple

from Dimensies.dimensie import Dimensie, DimensieList, DimensieLineage
from Dimensies.ambitie import Ambitie_Schema
from Dimensies.beleidsregel import BeleidsRegel_Schema
from Dimensies.doel import Doel_Schema
from Dimensies.provincialebelangen import ProvincialeBelangen_Schema
from Dimensies.beleidsrelaties import BeleidsRelatie_Schema
from Dimensies.maatregelen import Maatregelen_Schema
from Dimensies.themas import Themas_Schema
from Dimensies.opgaven import Opgaven_Schema
from Dimensies.verordening import Verordening_Schema

from Feiten.beleidsbeslissing import BeleidsBeslissing

from Dimensies.geothemas import Geothema
from Dimensies.gebruikers import Gebruiker
from Dimensies.werkingsgebieden import Werkingsgebied

from Auth.views import login, tokenstat
from Auth.commands import new_client_creds, new_client_creds_gebruikers

from Stats.views import stats

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from flask_cors import CORS

import json

from Stats.views import stats

current_version = '0.1'

# FLASK SETUP

app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = 'ZYhFfDSXvdAgkHXSu4NXtJAV8zoWRo8ki4XBtHffLuf4mx3rVxdev'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_HEADER_TYPE'] = "Token"
api = Api(app, prefix=f'/v{current_version}', decorators=[jwt_required,])
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

# (schema, slug, tablenaam, actuele_tablenaam, singular, plural)
dimensie_schemas = [(Ambitie_Schema, 'ambities','Ambities', 'Actuele_Ambities', 'Ambitie', 'Ambities'),
            (BeleidsRegel_Schema, 'beleidsregels', 'Beleidsregels', 'Actuele_Beleidsregels', 'Beleidsregel', 'Beleidsregels'),
            (Doel_Schema, 'doelen', 'Doelen', 'Actuele_Doelen', 'Doel', 'Doelen'),
            (ProvincialeBelangen_Schema, 'provincialebelangen', 'ProvincialeBelangen', 'Actuele_ProvincialeBelangen', 'Provinciaal Belang', 'Provinciale Belangen'),
            (BeleidsRelatie_Schema, 'beleidsrelaties', 'BeleidsRelaties', 'Actuele_BeleidsRelaties', 'Beleidsrelatie', 'Beleidsrelaties'),
            (Maatregelen_Schema, 'maatregelen', 'Maatregelen', 'Actuele_Maatregelen', 'Maatregel', 'Maatregelen'),
            (Themas_Schema, 'themas', 'Themas', 'Actuele_Themas', 'Thema', "Thema's"),
            (Opgaven_Schema,'opgaven', 'Opgaven', 'Actuele_Opgaven', 'Opgave', 'Opgaven'),
            (Verordening_Schema, 'verordeningen', 'Verordeningen', 'Actuele_Verordeningen', 'Verordening', 'Verordeningen')]

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

for schema, slug, tn, ac_tn, sn, pl in dimensie_schemas:
    schema_name = schema.__name__.split('_')[0]
    spec.components.schema(schema_name, schema=schema)
    api.add_resource(Dimensie, f'/{slug}/version/<string:uuid>', endpoint=schema_name,
        resource_class_args=(schema, tn, ac_tn))
    dimension_ept.append(schema_name)
    api.add_resource(DimensieList, f'/{slug}', endpoint=f"{schema_name}_lijst",
        resource_class_args=(schema, tn, ac_tn))
    dimension_ept.append(f"{schema_name}_lijst")
    api.add_resource(DimensieLineage, f'/{slug}/<int:id>', endpoint=f"{schema_name}_lineage", resource_class_args=(schema, tn))

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
                 'spec', lambda : json.dumps(spec.to_dict(), indent=2), methods=['GET'])  

api.add_resource(Werkingsgebied, '/werkingsgebieden',
                 '/werkingsgebieden/<string:werkingsgebied_uuid>')
api.add_resource(Geothema, '/geothemas',
                 '/geothemas/<string:geothema_uuid>')
api.add_resource(Gebruiker, '/gebruikers',
                 '/gebruikers/<string:gebruiker_uuid>')

api.add_resource(BeleidsBeslissing, '/beleidsbeslissingen',
                 '/beleidsbeslissingen/<string:beleidsbeslissing_uuid>')

if __name__ == '__main__':
    app.run()
