import marshmallow as MM
from .dimensie import Dimensie_Schema

class Opgaven_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True)
    Omschrijving = MM.fields.Str(missing=None)
    Weblink = MM.fields.Str(missing=None)