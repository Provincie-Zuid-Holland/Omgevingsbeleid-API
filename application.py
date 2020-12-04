import json
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from flask_restful import Api, Resource

import datamodel
from Auth.views import jwt_required_not_GET, login, tokenstat
from Dimensies.gebruikers import Gebruiker
from Feiten.feit import Feit, FeitenLineage, FeitenList
import Dimensies.dimensie
from Search.views import geo_search, search
from Special.verordeningsstructuur import Verordening_Structuur

current_version = '0.1'

# ENV SETUP
load_dotenv()

# FLASK SETUP
app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=4)
app.config['JWT_HEADER_TYPE'] = "Token"
api = Api(app, prefix=f'/v{current_version}',
          decorators=[jwt_required_not_GET, ])
jwt = JWTManager(app)


# JWT CONFIG
@jwt.unauthorized_loader
def custom_unauthorized_loader(reason):
    return jsonify(
        {"message": f"Authorisatie niet geldig: '{reason}'"}), 400

# ROUTING RULES
for dimensie in datamodel.dimensies:
    api.add_resource(Dimensies.dimensie.DimensieLineage, f'/{dimensie.slug}/<int:id>', endpoint=f'{dimensie.slug.capitalize()}_Lineage',
        resource_class_args=(dimensie.read_schema, dimensie.write_schema))
    
    api.add_resource(Dimensies.dimensie.DimensieList, f'/{dimensie.slug}', endpoint=f'{dimensie.slug.capitalize()}_List',
        resource_class_args=(dimensie.read_schema, dimensie.write_schema))

app.add_url_rule(f'/v{current_version}/login',
                 'login', login, methods=['POST'])
app.add_url_rule(f'/v{current_version}/tokeninfo',
                 'tokenstat', tokenstat, methods=['GET'])

# api.add_resource(Werkingsgebied, '/werkingsgebieden',
#                  '/werkingsgebieden/<string:werkingsgebied_uuid>')
api.add_resource(Gebruiker, '/gebruikers',
                 '/gebruikers/<string:gebruiker_uuid>')
# api.add_resource(Verordening_Structuur, '/verordeningstructuur',
#                  '/verordeningstructuur/<int:verordeningstructuur_id>',
#                  '/verordeningstructuur/version/<uuid:verordeningstructuur_uuid>')

# api.add_resource(feit_new.FeitenList, '/new_bbs', endpoint='New_bbs', resource_class_args=(Beleidsbeslissingen_Read_Schema, Beleidsbeslissingen_Read_Schema, feit_new.Kimball_Manager))

# api.add_resource(Vigerende_Maatregelen, '/maatregelen/vigerend')

if __name__ == '__main__':
    app.run()
