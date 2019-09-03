import marshmallow as MM
from .dimensie import Dimensie_Schema


class Belangen_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True)
    Omschrijving = MM.fields.Str(missing=None)
    Weblink = MM.fields.Str(missing=None)
    Type = MM.fields.Str(required=True, validate= [MM.validate.OneOf(['Nationaal Belang', 'Wettelijke Taak & Bevoegdheid']),])
