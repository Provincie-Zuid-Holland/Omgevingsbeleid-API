from flask import Flask
from flask_restful import Resource, Api
from ambitie import Ambitie

app = Flask(__name__)
api = Api(app, prefix='/v0')

api.add_resource(Ambitie, '/ambities', '/ambities/<string:ambitie_uuid>')

if __name__ == '__main__':
    app.run()