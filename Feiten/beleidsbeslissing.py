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

    class Meta:
        ordered = True
