import marshmallow as MM
from .dimensie import Dimensie_Schema
from globals import default_user_uuid

class Verordening_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Inhoud = MM.fields.Str(missing=None, obprops=['search_field'])
    Status = MM.fields.Str(required=True, obprops=[])
    Type = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Hoofdstuk', 'Afdeling', 'Paragraaf', 'Artikel', 'Lid']), ], obprops=[])
    Volgnummer = MM.fields.Str(required=True, obprops=[])
    Werkingsgebied = MM.fields.UUID(missing=default_user_uuid, attribute='fk_Werkingsgebied', obprops=['geo_field'])
    Weblink = MM.fields.Str(missing=None, search_field="text", obprops=[])
    Eigenaar_1 = MM.fields.UUID(required=False, missing=default_user_uuid, obprops=[])
    Eigenaar_2 = MM.fields.UUID(required=False, missing=default_user_uuid, obprops=[])
    Portefeuillehouder_1 = MM.fields.UUID(required=False, missing=default_user_uuid, obprops=[])
    Portefeuillehouder_2 = MM.fields.UUID(required=False, missing=default_user_uuid, obprops=[])
    Opdrachtgever = MM.fields.UUID(required=False, missing=default_user_uuid, obprops=[])

    @MM.post_dump()
    def remove_carriage_returns(self, data, many,):
        if 'Inhoud' in data:
            data['Inhoud'] = data['Inhoud'].replace('\r', '\n')
        return data