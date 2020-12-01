import marshmallow as MM
from .dimensie import Dimensie_Schema


class Ambitie_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Weblink = MM.fields.Str(missing=None, obprops=[])

    class Meta(Dimensie_Schema.Meta):
        table= 'Ambities'
        read_only = False
        ordered = True
        searchable = True
