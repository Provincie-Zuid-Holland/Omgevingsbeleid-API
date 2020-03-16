import marshmallow as MM
from .dimensie import Dimensie_Schema


class Belangen_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Weblink = MM.fields.Str(missing=None, obprops=[ ])
    Type = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Nationaal Belang', 'Wettelijke Taak & Bevoegdheid']), ], obprops=[])
