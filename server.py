from flask import Flask, jsonify
from flask_restful import Resource, Api
from flasgger import Swagger
from apispec import APISpec
from apispec.ext.flask import FlaskPlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from pprint import pprint

from Dimensies.ambitie import Ambitie
from Dimensies.beleidsregel import BeleidsRegel
from Dimensies.doel import Doel
from Dimensies.provinciaalbelang import ProvinciaalBelang
from Dimensies.thema import Thema
from Dimensies.opgaven import Opgave
from Dimensies.maatregelen import Maatregel, Maatregelen_Schema
from Dimensies.verordening import Verordening
from Dimensies.werkingsgebieden import Werkingsgebied
from Dimensies.geothemas import Geothema
from Dimensies.beleidsrelaties import BeleidsRelatie


from Feiten.beleidsbeslissing import BeleidsBeslissing

current_version = '0.1'

app = Flask(__name__)
api = Api(app, prefix=f'/v{current_version}')


api.add_resource(Ambitie, '/ambities', '/ambities/<string:ambitie_uuid>')
api.add_resource(BeleidsRegel, '/beleidsregels', '/beleidsregels/<string:beleidsregel_uuid>')
api.add_resource(Doel, '/doelen', '/doelen/<string:doel_uuid>')
api.add_resource(ProvinciaalBelang, '/provincialebelangen', '/provincialebelangen/<string:provinciaalbelang_uuid>')
api.add_resource(Thema, '/themas', '/themas/<string:thema_uuid>')
api.add_resource(Opgave, '/opgaven', '/opgaven/<string:opgave_uuid>')
api.add_resource(Maatregel, '/maatregelen', '/maatregelen/<string:maatregel_uuid>')
api.add_resource(Verordening, '/verordeningen', '/verordeningen/<string:verordening_uuid>')
api.add_resource(Werkingsgebied, '/werkingsgebieden', '/werkingsgebieden/<string:werkingsgebied_uuid>')
api.add_resource(Geothema, '/geothemas', '/geothemas/<string:geothema_uuid>')
api.add_resource(BeleidsRelatie, '/beleidsrelaties', '/beleidsrelaties/<string:beleidsrelatie_uuid>')

api.add_resource(BeleidsBeslissing, '/beleidsbeslissingen', '/beleidsbeslissingen/<string:beleidsbeslissing_uuid>')
if __name__ == '__main__':
    app.run()