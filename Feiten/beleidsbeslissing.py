import marshmallow as MM
from .feit import Feiten_Schema, Link_Schema


class Beleidsbeslissingen_Meta_Schema(Feiten_Schema):
    Eigenaar_1 = MM.fields.UUID(required=True)
    Eigenaar_2 = MM.fields.UUID(required=True)
    Portefeuillehouder = MM.fields.UUID(required=True)
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
    ProvincialeBelangen = MM.fields.Nested(
        Link_Schema, many=True, default=[], missing=[])
    Opgaven = MM.fields.Nested(Link_Schema, many=True, default=[], missing=[])


class Beleidsbeslissingen_Read_Schema(Feiten_Schema):
    Eigenaar_1 = MM.fields.UUID(required=True, linker=False)
    Eigenaar_2 = MM.fields.UUID(required=True, linker=False)
    Portefeuillehouder_1 = MM.fields.UUID(required=True, linker=False)
    Portefeuillehouder_2 = MM.fields.UUID(required=True, linker=False)
    Opdrachtgever = MM.fields.UUID(required=True, linker=False)
    Status = MM.fields.Str(required=True, linker=False)
    Titel = MM.fields.Str(required=True, linker=False)
    Omschrijving_Keuze = MM.fields.Str(missing=None, linker=False)
    Omschrijving_Werking = MM.fields.Str(missing=None, linker=False)
    Aanleiding = MM.fields.Str(missing=None, linker=False)
    Afweging = MM.fields.Str(missing=None, linker=False)
    Provinciaal_Belang = MM.fields.Str(missing=None, linker=False)
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

    class Meta:
        ordered = True
