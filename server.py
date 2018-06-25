from flask import Flask
from flask_restful import Resource, Api
from ambitie import Ambitie
from flask_restful_swagger import swagger

app = Flask(__name__)
api = swagger.docs(Api(app), apiVersion= '0.0', api_spec_url='/api/spec')

api.add_resource(Ambitie, '/ambities', '/ambities/<string:ambitie_uuid>')

if __name__ == '__main__':
    app.run()