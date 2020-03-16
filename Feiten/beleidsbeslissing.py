import marshmallow as MM
from globals import default_user_uuid

from .feit import Feiten_Schema, Link_Schema


class Beleidsbeslissingen_Meta_Schema(Feiten_Schema):
    Eigenaar_1 = MM.fields.UUID(missing=default_user_uuid)
    Eigenaar_2 = MM.fields.UUID(missing=default_user_uuid)
    Portefeuillehouder = MM.fields.UUID(missing=default_user_uuid)
    Status = MM.fields.Str(required=True)
    Titel = MM.fields.Str(required=True)
    Omschrijving_Keuze = MM.fields.Str(missing=None)
    Omschrijving_Werking = MM.fields.Str(missing=None)
    Motivering = MM.fields.Str(missing=None)
    Aanleiding = MM.fields.Str(missing=None)
    Afweging = MM.fields.Str(missing=None)
    Verordening_Realisatie = MM.fields.Str(missing=None)


class Beleidsbeslissingen_Fact_Schema(Feiten_Schema):
    Beleidsbeslissing = MM.fields.UUID(
        required=True, attribute='fk_Beleidsbeslissingen')
    WerkingsGebieden = MM.fields.Nested(
        Link_Schema, many=True, default=[], missing=[])
    BeleidsRegels = MM.fields.Nested(
        Link_Schema, many=True,  default=[], missing=[])
    Verordening = MM.fields.Nested(
        Link_Schema, many=True,  default=[], missing=[])
    Maatregelen = MM.fields.Nested(
        Link_Schema, many=True,  default=[], missing=[])
    Themas = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[])
    Ambities = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[])
    Doelen = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[])
    Belangen = MM.fields.Nested(
        Link_Schema, many=True, default=[], missing=[])
    Opgaven = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[])


class Beleidsbeslissingen_Read_Schema(Feiten_Schema):
    Eigenaar_1 = MM.fields.UUID(default=default_user_uuid, missing=default_user_uuid, allow_none=True, userfield=True, obprops=['userfield'])
    Eigenaar_2 = MM.fields.UUID(default=default_user_uuid, missing=default_user_uuid, allow_none=True, userfield=True, obprops=['userfield'])
    Portefeuillehouder_1 = MM.fields.UUID(default=default_user_uuid, missing=default_user_uuid, allow_none=True, obprops=['userfield'])
    Portefeuillehouder_2 = MM.fields.UUID(default=default_user_uuid, missing=default_user_uuid, allow_none=True, obprops=['userfield'])
    Opdrachtgever = MM.fields.UUID(default=default_user_uuid, missing=default_user_uuid, allow_none=True, obprops=['userfield'])
    Status = MM.fields.Str(required=True, obprops=[])
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving_Keuze = MM.fields.Str(missing=None, obprops=['search_field'])
    Omschrijving_Werking = MM.fields.Str(missing=None, obprops=['search_field'])
    Aanleiding = MM.fields.Str(missing=None, obprops=['search_field'])
    Afweging = MM.fields.Str(missing=None, obprops=['search_field'])
    Provinciaal_Belang = MM.fields.Str(missing=None, obprops=['search_field'])
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Besluitnummer = MM.fields.Str(missing=None, obprops=[])
    Tags = MM.fields.Str(missing=None, obprops=[])
    WerkingsGebieden = MM.fields.Nested(
        Link_Schema, many=True, default=[], missing=[], obprops=['linker'])
    BeleidsRegels = MM.fields.Nested(
        Link_Schema, many=True,  default=[], missing=[], obprops=['linker'])
    Verordening = MM.fields.Nested(
        Link_Schema, many=True,  default=[], missing=[], obprops=['linker'])
    Maatregelen = MM.fields.Nested(
        Link_Schema, many=True,  default=[], missing=[], obprops=['linker'])
    Themas = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], obprops=['linker'])
    Ambities = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], obprops=['linker'])
    Doelen = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], obprops=['linker'])
    Belangen = MM.fields.Nested(
        Link_Schema, many=True, default=[], missing=[], obprops=['linker'])
    Opgaven = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], obprops=['linker'])

    def default_user(self, data):
        for field in self.fields_with_props('userfield'):
            if data.get(field) == default_user_uuid:
                data[field] = None
        return data

    @MM.post_dump(pass_many=True)
    def default_user_many(self, data, many):
        if many:
            return list(map(self.default_user, data))
        else:
            return self.default_user(data)

    def none_to_nullUUID(self, data):
        for field in self.fields_with_props('userfield'):
            if data.get(field) == None:
                data[field] = default_user_uuid
        return data
    
    @MM.post_load()
    def none_to_nullUUID_many(self, data, many, partial):
        if many:
            return list(map(self.none_to_nullUUID, data))
        else:
            return self.none_to_nullUUID(data)

    class Meta:
        ordered = True
