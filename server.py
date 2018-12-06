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
# from Dimensies.beleidsregel import BeleidsRegel
from Dimensies.doel import Doel_Schema
# from Dimensies.provinciaalbelang import ProvinciaalBelang
# from Dimensies.thema import Thema
# from Dimensies.opgaven import Opgave
# from Dimensies.maatregelen import Maatregel, Maatregelen_Schema
# from Dimensies.verordening import Verordening
# from Dimensies.werkingsgebieden import Werkingsgebied
# from Dimensies.geothemas import Geothema
# from Dimensies.beleidsrelaties import BeleidsRelatie
# from Dimensies.gebruikers import Gebruiker

# from Feiten.beleidsbeslissing import BeleidsBeslissing

from Auth.views import login
from Auth.commands import new_client_creds

current_version = '0.1'

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'ZYhFfDSXvdAgkHXSu4NXtJAV8zoWRo8ki4XBtHffLuf4mx3rVx'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_HEADER_TYPE'] = "Token"
api = Api(app, prefix=f'/v{current_version}')
jwt = JWTManager(app)


@jwt.unauthorized_loader
def custom_unauthorized_loader(reason):
    return jsonify(
        {"message": f"Authorisatie niet geldig: '{reason}'"}), 400


# Custom commands
@app.cli.command()
@click.argument('client_identifier')
def generate_client_creds(client_identifier):
    result = new_client_creds(client_identifier)
    click.echo(result)
    click.pause()


app.add_url_rule(f'/v{current_version}/login',
                 'login', login, methods=['POST'])


# schema = naam van schema (moet erven van Dimensie_schema)
# single = Naam van dimensie in enkelvoud
# all = Naam van dimensie in meervoud
# actueel = Optionele tablenaam voor een 'actuele' view

# Dimensie_record = namedtuple('Dimensie_record', ['schema', 'single', 'all', 'actueel'])

# dimensies = [
#     Dimensie_record(Ambitie_Schema, 'Ambitie','Ambities', 'Actuele_Ambities')
# ]

api.add_resource(Dimensie, '/ambities', '/ambities/<string:uuid>', endpoint='Ambities',
                 resource_class_args=(Ambitie_Schema, 'Ambities', 'Actuele_Ambities'))

api.add_resource(Dimensie, '/doelen', '/doelen/<string:uuid>', endpoint='Doelen',
                 resource_class_args=(Doel_Schema, 'Doelen', 'Actuele_Doelen'))
# api.add_resource(BeleidsRegel, '/beleidsregels',
#                  '/beleidsregels/<string:beleidsregel_uuid>')
# api.add_resource(Doel, '/doelen',
#                  '/doelen/<string:doel_uuid>')
# api.add_resource(ProvinciaalBelang, '/provincialebelangen',
#                  '/provincialebelangen/<string:provinciaalbelang_uuid>')
# api.add_resource(Thema, '/themas',
#                  '/themas/<string:thema_uuid>')
# api.add_resource(Opgave, '/opgaven',
#                  '/opgaven/<string:opgave_uuid>')
# api.add_resource(Maatregel, '/maatregelen',
#                  '/maatregelen/<string:maatregel_uuid>')
# api.add_resource(Verordening, '/verordeningen',
#                  '/verordeningen/<string:verordening_uuid>')
# api.add_resource(Werkingsgebied, '/werkingsgebieden',
#                  '/werkingsgebieden/<string:werkingsgebied_uuid>')
# api.add_resource(Geothema, '/geothemas',
#                  '/geothemas/<string:geothema_uuid>')
# api.add_resource(BeleidsRelatie, '/beleidsrelaties',
#                  '/beleidsrelaties/<string:beleidsrelatie_uuid>')
# api.add_resource(Gebruiker, '/gebruikers',
#                  '/gebruikers/<string:gebruiker_uuid>')
# api.add_resource(BeleidsBeslissing, '/beleidsbeslissingen',
#                  '/beleidsbeslissingen/<string:beleidsbeslissing_uuid>')

if __name__ == '__main__':
    app.run()
