import marshmallow as MM
from .dimensie import Dimensie_Schema

class Verordening_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True, search_field="text")
    Inhoud = MM.fields.Str(missing=None, search_field="text")
    Status = MM.fields.Str(required=True)
    Type = MM.fields.Str(required=True, validate= [MM.validate.OneOf(['Hoofdstuk', 'Afdeling', 'Paragraaf', 'Artikel']),])
    Volgnummer = MM.fields.Str(required=True)
    Werkingsgebied = MM.fields.UUID(missing=None, attribute= 'fk_Werkingsgebied')
    Eigenaar_1 = MM.fields.UUID(required=False)
    Eigenaar_2 = MM.fields.UUID(required=False)
    Portefeuillehouder_1 = MM.fields.UUID(required=False)
    Portefeuillehouder_2 = MM.fields.UUID(required=False)
    Opdrachtgever = MM.fields.UUID(required=False)