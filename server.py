from flask import Flask
from flask_restful import Resource, Api
from flasgger import Swagger

from Dimensies.ambitie import Ambitie

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

if __name__ == '__main__':
    app.run()