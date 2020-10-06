import marshmallow as MM
from endpoints.endpoint import Default_Schema


class Ambitie_Schema(Default_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Weblink = MM.fields.Str(missing=None, obprops=[])

    class Meta(Default_Schema.Meta):
        table = 'Ambities'
        read_only = False
        searchable = True