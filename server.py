from flask import Flask
from flask_restful import Resource, Api
from flasgger import Swagger

from Dimensies.ambitie import Ambitie
from Dimensies.beleidsregel import BeleidsRegel
from Dimensies.doel import Doel
from Dimensies.provinciaalbelang import ProvinciaalBelang
from Dimensies.thema import Thema
current_version = '0.1'

app = Flask(__name__)
api = Api(app, prefix=f'/v{current_version}')
# swagger = Swagger(app, config= {
    # 'headers':[],
    # 'specs':[{
        # 'endpoint':f'apispec_1',
        # 'route':f'/apispec_1.json',
        # 'rule_filter': lambda rule: True,
        # 'model_filter': lambda model: True,
    # }],
    # 'static_url_path' : '/flasgger_static',
    # 'swagger_ui': True,
    # 'specs_route': f'/v{current_version}/apidocs/'
# })
swagger = Swagger(app)

api.add_resource(Ambitie, '/ambities', '/ambities/<string:ambitie_uuid>')
api.add_resource(BeleidsRegel, '/beleidsregels', '/beleidsregels/<string:beleidsregel_uuid>')
api.add_resource(Doel, '/doelen', '/doelen/<string:doel_uuid>')
api.add_resource(ProvinciaalBelang, '/provincialebelangen', '/provincialebelangen/<string:provinciaalbelang_uuid>')
api.add_resource(Thema, '/themas', '/themas/<string:thema_uuid>')

if __name__ == '__main__':
    app.run()