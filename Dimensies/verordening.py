import marshmallow as MM
from .dimensie import Dimensie_Schema
from globals import default_user_uuid

class Verordening_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True, search_field="text")
    Inhoud = MM.fields.Str(missing=None, search_field="text")
    Status = MM.fields.Str(required=True)
    Type = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Hoofdstuk', 'Afdeling', 'Paragraaf', 'Artikel']), ])
    Volgnummer = MM.fields.Str(required=True)
    Werkingsgebied = MM.fields.UUID(missing=None, attribute='fk_Werkingsgebied')
    Weblink = MM.fields.Str(missing=None, search_field="text")
    Eigenaar_1 = MM.fields.UUID(required=False, missing=default_user_uuid)
    Eigenaar_2 = MM.fields.UUID(required=False, missing=default_user_uuid)
    Portefeuillehouder_1 = MM.fields.UUID(required=False, missing=default_user_uuid)
    Portefeuillehouder_2 = MM.fields.UUID(required=False, missing=default_user_uuid)
    Opdrachtgever = MM.fields.UUID(required=False, missing=default_user_uuid)
