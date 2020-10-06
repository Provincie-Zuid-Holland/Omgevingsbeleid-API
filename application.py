import json
import os
from datetime import timedelta

import click
from flask import Flask, jsonify

from Auth.views import login, tokenstat, jwt_required_not_GET
from datamodel import dimensies, feiten
from Dimensies.dimensie import Dimensie, DimensieLineage, DimensieList
from Dimensies.gebruikers import Gebruiker
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
from errors import errors
from Dimensies.maatregelen import Vigerende_Maatregelen
from dotenv import load_dotenv
import endpoints
import endpoints.datamodel as dm
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
          decorators=[jwt_required_not_GET, ], errors=errors)

api2 = Api(app, prefix=f'/v0.2',
          decorators=[jwt_required_not_GET, ], errors=errors)

jwt = JWTManager(app)


app.add_url_rule(f'/v{current_version}/search',
                 'search', search, methods=['GET'])
app.add_url_rule(f'/v{current_version}/search/geo',
                 'geo-search', geo_search, methods=['GET'])


# JWT CONFIG
@jwt.unauthorized_loader
def custom_unauthorized_loader(reason):
    return jsonify(
        {"message": f"Authorisatie niet geldig: '{reason}'"}), 400

# ROUTING RULES (v0.1)

dimension_ept = []

for dimensie in dimensies:
    api.add_resource(Dimensie, f'/{dimensie["slug"]}/version/<string:uuid>', endpoint=dimensie['singular'],
                     resource_class_args=(dimensie['schema'], dimensie['tablename'], dimensie['latest_tablename']))
    dimension_ept.append(dimensie['singular'])
    api.add_resource(DimensieList, f'/{dimensie["slug"]}', endpoint=f"{dimensie['plural']}_lijst",
                     resource_class_args=(dimensie['schema'], dimensie['tablename'], dimensie['latest_tablename']))
    dimension_ept.append(f"{dimensie['plural']}_lijst")
    api.add_resource(DimensieLineage, f'/{dimensie["slug"]}/<int:id>', endpoint=f"{dimensie['plural']}_lineage",
                     resource_class_args=(dimensie['schema'],  dimensie['tablename']))

for feit in feiten:
    general_args = (feit['meta_schema'], feit['meta_tablename'], feit['meta_tablename_actueel'], feit['meta_tablename_vigerend'],
                    feit['fact_schema'], feit['fact_tablename'], feit['fact_view'], feit['fact_to_meta_field'], feit['read_schema'])
    api.add_resource(FeitenList, f'/{feit["slug"]}', endpoint=f'{feit["slug"]}_lijst',
                     resource_class_args=general_args)
    api.add_resource(FeitenLineage, f'/{feit["slug"]}/<string:id>', endpoint=f'{feit["slug"]}_lineage',
                     resource_class_args=general_args)
    api.add_resource(Feit, f'/{feit["slug"]}/version/<string:uuid>', endpoint=f'{feit["slug"]}',
                     resource_class_args=general_args)

app.add_url_rule(f'/v{current_version}/login',
                 'login', login, methods=['POST'])
app.add_url_rule(f'/v{current_version}/tokeninfo',
                 'tokenstat', tokenstat, methods=['GET'])
app.add_url_rule(f'/v{current_version}/stats',
                 'stats', stats, methods=['GET'])

api.add_resource(Werkingsgebied, '/werkingsgebieden',
                 '/werkingsgebieden/<string:werkingsgebied_uuid>')
api.add_resource(Gebruiker, '/gebruikers',
                 '/gebruikers/<string:gebruiker_uuid>')
api.add_resource(Verordening_Structuur, '/verordeningstructuur',
                 '/verordeningstructuur/<int:verordeningstructuur_id>',
                 '/verordeningstructuur/version/<uuid:verordeningstructuur_uuid>')

api.add_resource(Vigerende_Maatregelen, '/maatregelen/vigerend')

# ROUTING RULES (v0.2)
for ep in dm.endpoints:
    api2.add_resource(endpoints.endpoint.Lineage_Endpoint, f'/{ep.slug}/<int:id>', endpoint=f'{ep.slug.capitalize()}_Lineage',
        resource_class_args=(ep.read_schema, ep.write_schema))

    api2.add_resource(endpoints.endpoint.List_Endpoint, f'/{ep.slug}', endpoint=f'{ep.slug.capitalize()}_List',
        resource_class_args=(ep.read_schema, ep.write_schema))

    api2.add_resource(endpoints.endpoint.Version_Endpoint, f'/{ep.slug}/version/<string:uuid>', endpoint=f'{ep.slug.capitalize()}_Version',
        resource_class_args=(ep.read_schema, ep.write_schema))


if __name__ == '__main__':
    app.run()
