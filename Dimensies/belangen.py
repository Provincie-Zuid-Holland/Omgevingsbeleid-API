import marshmallow as MM
from .dimensie import Dimensie_Schema


class Belangen_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True, search_field="text")
    Omschrijving = MM.fields.Str(missing=None, search_field="text")
    Weblink = MM.fields.Str(missing=None, search_field="text")
    Type = MM.fields.Str(required=True, validate= [MM.validate.OneOf(['Nationaal Belang', 'Wettelijke Taak & Bevoegdheid']),])
