import marshmallow as MM
from .dimensie import Dimensie_Schema


class BeleidsRegel_Schema(Dimensie_Schema):

    Titel = MM.fields.Str(required=True, search_field="text")
    Omschrijving = MM.fields.Str(missing=None, search_field="text")
    Weblink = MM.fields.Str(missing=None, search_field="text")