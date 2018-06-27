from flask import Flask
from flask_restful import Resource, Api
from flasgger import Swagger

from Dimensies.ambitie import Ambitie
from Dimensies.beleidsregel import BeleidsRegel
from Dimensies.doel import Doel
from Dimensies.provinciaalbelang import ProvinciaalBelang
from Dimensies.thema import Thema
from Feiten.beleidsbeslissing import BeleidsBeslissing
current_version = '0.1'

app = Flask(__name__)
api = Api(app, prefix=f'/v{current_version}')

swagger_template = {
    'swagger': '3.0',
    'info': {
        'title': 'Omgevingsbeleid API',
        'info': 'API voor het project digitaal omgevingsbeleid van de Provincie Zuid-Holland',
        'contact': {
            'responsibleOrganization': 'Provincie Zuid-Holland',
            'responsibleDeveloper': 'Swen Mulderij',
            'email': 'swenmulderij@gmail.com',
            },
        },
    }
        
            
swagger = Swagger(app, template=swagger_template)

api.add_resource(Ambitie, '/ambities', '/ambities/<string:ambitie_uuid>')
api.add_resource(BeleidsRegel, '/beleidsregels', '/beleidsregels/<string:beleidsregel_uuid>')
api.add_resource(Doel, '/doelen', '/doelen/<string:doel_uuid>')
api.add_resource(ProvinciaalBelang, '/provincialebelangen', '/provincialebelangen/<string:provinciaalbelang_uuid>')
api.add_resource(Thema, '/themas', '/themas/<string:thema_uuid>')
api.add_resource(BeleidsBeslissing, '/beleidsbeslissingen', '/beleidsbeslissingen/<string:beleidsbeslissing_uuid>')
if __name__ == '__main__':
    app.run()