import marshmallow as MM
from .dimensie import Dimensie_Schema

class Verordening_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True)
    Omschrijving = MM.fields.Str(missing=None)
    Status = MM.fields.Str(required=True)
    Type = MM.fields.Str(required=True, validate= [MM.validate.OneOf(['Hoofdstuk', 'Afdeling', 'Paragraaf', 'Artikel']),])
    Volgnummer = MM.fields.Str(required=True)
    Werkingsgebied = MM.fields.UUID(missing=None, attribute= 'fk_Werkingsgebied')