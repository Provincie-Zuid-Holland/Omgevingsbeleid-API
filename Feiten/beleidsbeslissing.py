import marshmallow as MM
from .feit import Feiten_Schema, Link_Schema
from globals import default_user_uuid

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
    Eigenaar_1 = MM.fields.UUID(default=default_user_uuid, missing=default_user_uuid, allow_none=True, linker=False, userfield=True)
    Eigenaar_2 = MM.fields.UUID(default=default_user_uuid, missing=default_user_uuid, allow_none=True, linker=False, userfield=True)
    Portefeuillehouder_1 = MM.fields.UUID(default=default_user_uuid, missing=default_user_uuid, allow_none=True, linker=False, userfield=True)
    Portefeuillehouder_2 = MM.fields.UUID(default=default_user_uuid, missing=default_user_uuid, allow_none=True, linker=False, userfield=True)
    Opdrachtgever = MM.fields.UUID(default=default_user_uuid, missing=default_user_uuid, allow_none=True, linker=False, userfield=True)
    Status = MM.fields.Str(required=True, linker=False)
    Titel = MM.fields.Str(required=True, linker=False, search_field="text")
    Omschrijving_Keuze = MM.fields.Str(missing=None, linker=False, search_field="text")
    Omschrijving_Werking = MM.fields.Str(missing=None, linker=False, search_field="text")
    Aanleiding = MM.fields.Str(missing=None, linker=False, search_field="text")
    Afweging = MM.fields.Str(missing=None, linker=False, search_field="text")
    Provinciaal_Belang = MM.fields.Str(missing=None, linker=False, search_field="text")
    Weblink = MM.fields.Str(missing=None, linker=False)
    Besluitnummer = MM.fields.Str(missing=None)
    Tags = MM.fields.Str(missing=None)
    WerkingsGebieden = MM.fields.Nested(
        Link_Schema, many=True, default=[], missing=[], linker=True)
    BeleidsRegels = MM.fields.Nested(
        Link_Schema, many=True,  default=[], missing=[], linker=True)
    Verordening = MM.fields.Nested(
        Link_Schema, many=True,  default=[], missing=[], linker=True)
    Maatregelen = MM.fields.Nested(
        Link_Schema, many=True,  default=[], missing=[], linker=True)
    Themas = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], linker=True)
    Ambities = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], linker=True)
    Doelen = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], linker=True)
    Belangen = MM.fields.Nested(
        Link_Schema, many=True, default=[], missing=[], linker=True)
    Opgaven = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[], linker=True)

    def default_user(self, data):
        for field in self.fields:
            if data.get(field) == default_user_uuid and "userfield" in self.fields[field].metadata and self.fields[field].metadata['userfield']:
                data[field] = None
        return data

    @MM.post_dump(pass_many=True)
    def default_user_many(self, data, many):
        if many:
            return list(map(self.default_user, data))
        else:
            return self.default_user(data)

    def none_to_nullUUID(self, data):
        for field in self.fields:
            if data.get(field) == None and "userfield" in self.fields[field].metadata and self.fields[field].metadata['userfield']:
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
