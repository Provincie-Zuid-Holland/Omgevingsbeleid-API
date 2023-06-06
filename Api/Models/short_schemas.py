import marshmallow as MM

from Api.Endpoints.base_schema import Short_Base_Schema

# For reverse lookups we have to define a custom schema in order to prevent circulair imports
class Short_Beleidskeuze_Schema(Short_Base_Schema):
    ID = MM.fields.Integer(required=True, obprops=[])
    UUID = MM.fields.UUID(required=True, obprops=[])
    Titel = MM.fields.Str(required=True, obprops=[])

    class Meta(Short_Base_Schema.Meta):
        slug = "beleidskeuze-short"
        status_conf = ("Status", "Vigerend")


class Short_Beleidsmodule_Schema(Short_Base_Schema):
    Titel = MM.fields.Str(required=True, obprops=[])

    class Meta(Short_Base_Schema.Meta):
        slug = "beleidsmodule-short"


class Short_Gebiedsprogramma_Schema(Short_Base_Schema):
    ID = MM.fields.Integer(required=True, obprops=[])
    UUID = MM.fields.UUID(required=True, obprops=[])
    Titel = MM.fields.Str(required=True, obprops=[])

    class Meta(Short_Base_Schema.Meta):
        slug = "gebiedsprogramma-short"
        status_conf = ("Status", "Vigerend")


class Short_Beleidsdoel_Schema(Short_Base_Schema):
    ID = MM.fields.Integer(required=True, obprops=[])
    UUID = MM.fields.UUID(required=True, obprops=[])
    Titel = MM.fields.Str(required=True, obprops=[])

    class Meta(Short_Base_Schema.Meta):
        slug = "beleidsdoel-short"
