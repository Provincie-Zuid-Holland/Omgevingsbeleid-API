from flask import Flask, jsonify
from flask_restful import Resource, Api
from pprint import pprint
from datetime import timedelta
from flask_jwt_extended import (
    JWTManager, jwt_required
)
import click
from collections import namedtuple

from Dimensies.dimensie import Dimensie
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

from Auth.views import login
from Auth.commands import new_client_creds

from Stats.views import stats

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
current_version = '0.1'

# FLASK SETUP

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'ZYhFfDSXvdAgkHXSu4NXtJAV8zoWRo8ki4XBtHffLuf4mx3rVx'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_HEADER_TYPE'] = "Token"
api = Api(app, prefix=f'/v{current_version}')
jwt = JWTManager(app)

# APISPEC SETUP

spec = APISpec(
    title='Omgevingsbeleid service',
    version=current_version,
    openapi_version='2.0',
    plugins=[
        MarshmallowPlugin(), 
        FlaskPlugin()
        ]
)

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

# ROUTING RULES

app.add_url_rule(f'/v{current_version}/login',
                 'login', login, methods=['POST'])
app.add_url_rule(f'/v{current_version}/stats',
                 'stats', stats, methods=['GET'])

api.add_resource(Dimensie, '/ambities', '/ambities/<string:uuid>', endpoint='Ambities',
                 resource_class_args=(Ambitie_Schema, 'Ambities', 'Actuele_Ambities'))

api.add_resource(Dimensie, '/doelen', '/doelen/<string:uuid>', endpoint='Doelen',
                 resource_class_args=(Doel_Schema, 'Doelen', 'Actuele_Doelen'))

api.add_resource(Dimensie, '/beleidsregels', '/beleidsregels/<string:uuid>', endpoint='Beleidsregels',
                 resource_class_args=(BeleidsRegel_Schema, 'BeleidsRegels', 'Actuele_BeleidsRegels'))                 

api.add_resource(Dimensie, '/provincialebelangen', '/provincialebelangen/<string:uuid>', endpoint='Provincialebelangen',
                 resource_class_args=(ProvincialeBelangen_Schema, 'ProvinicialeBelangen', 'Actuele_ProvincialeBelangen'))

api.add_resource(Dimensie, '/beleidsrelaties', '/beleidsrelaties/<string:uuid>', endpoint='Beleidsrelaties',
                 resource_class_args=(BeleidsRelatie_Schema, 'BeleidsRelaties', 'Actuele_BeleidsRelaties'))

api.add_resource(Dimensie, '/maatregelen', '/maatregelen/<string:uuid>', endpoint='Maatregelen', 
                 resource_class_args=(Maatregelen_Schema, 'Maatregelen', 'Actuele_Maatregelen'))

api.add_resource(Dimensie, '/themas', '/themas/<string:uuid>', endpoint='Themas', 
                 resource_class_args=(Themas_Schema, 'Themas', 'Actuele_Themas'))                 

api.add_resource(Dimensie, '/opgaven', '/opgaven/<string:uuid>', endpoint='Opgaven', 
                 resource_class_args=(Opgaven_Schema, 'Opgaven', 'Actuele_Opgaven'))                 

api.add_resource(Dimensie, '/verordeningen', '/verordeningen/<string:uuid>', endpoint='Verordeningen',
                 resource_class_args=(Verordening_Schema, 'Verordeningen', 'Actuele_Verordeningen'))

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
