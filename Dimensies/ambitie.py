import marshmallow as MM
from .dimensie import Dimensie_Schema
from elasticsearch_dsl import connections, Index, Document, Text, Integer


class Ambitie_Schema(Dimensie_Schema):

    Titel = MM.fields.Str(required=True, search_field="text")
    Omschrijving = MM.fields.Str(missing=None, search_field="text")
    Weblink = MM.fields.Str(missing=None, search_field="text")
