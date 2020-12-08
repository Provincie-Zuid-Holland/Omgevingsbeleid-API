import marshmallow as MM
from Endpoints.normal import Normal_Schema


class Ambitie_Schema(Normal_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Weblink = MM.fields.Str(missing=None, obprops=[])

    class Meta(Normal_Schema.Meta):
        table= 'Ambities'
        read_only = False
        ordered = True
        searchable = True
