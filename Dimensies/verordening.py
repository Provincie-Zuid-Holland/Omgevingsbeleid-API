import marshmallow as MM
from .dimensie import Dimensie_Schema
from globals import default_user_uuid

class Verordening_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Inhoud = MM.fields.Str(missing=None, obprops=['search_field'])
    Status = MM.fields.Str(required=True, obprops=[])
    Type = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Hoofdstuk', 'Afdeling', 'Paragraaf', 'Artikel']), ], obprops=[])
    Volgnummer = MM.fields.Str(required=True, obprops=[])
    Werkingsgebied = MM.fields.UUID(missing=None, attribute='fk_Werkingsgebied', obprops=[])
    Weblink = MM.fields.Str(missing=None, search_field="text", obprops=[])
    Eigenaar_1 = MM.fields.UUID(required=False, missing=default_user_uuid, obprops=[])
    Eigenaar_2 = MM.fields.UUID(required=False, missing=default_user_uuid, obprops=[])
    Portefeuillehouder_1 = MM.fields.UUID(required=False, missing=default_user_uuid, obprops=[])
    Portefeuillehouder_2 = MM.fields.UUID(required=False, missing=default_user_uuid, obprops=[])
    Opdrachtgever = MM.fields.UUID(required=False, missing=default_user_uuid, obprops=[])
