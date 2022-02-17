# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import marshmallow.fields as MMF

from Api.Models.gebruikers import Gebruikers_Schema
from Api.Models.beleidskeuzes import Beleidskeuzes_Schema
from Api.Models.ambities import Ambities_Schema
from Api.Models.belangen import Belangen_Schema
from Api.Models.beleidsdoelen import Beleidsdoelen_Schema
from Api.Models.beleidsprestaties import Beleidsprestaties_Schema
from Api.Models.beleidsregels import Beleidsregels_Schema
from Api.Models.maatregelen import Maatregelen_Schema
from Api.Models.themas import Themas_Schema
from Api.Models.werkingsgebieden import Werkingsgebieden_Schema
from Api.Models.verordeningen import Verordeningen_Schema
from Api.Models.beleidsrelaties import Beleidsrelaties_Schema
from Api.Models.beleidsmodule import Beleidsmodule_Schema
from Api.Models.short_schemas import Short_Beleidsmodule_Schema, Short_Beleidskeuze_Schema
import Api.Endpoints.references as references

short_schemas = [Short_Beleidskeuze_Schema, Short_Beleidsmodule_Schema]

endpoints = [
    Beleidsrelaties_Schema,
    Beleidsmodule_Schema,
    Beleidskeuzes_Schema,
    Ambities_Schema,
    Belangen_Schema,
    Beleidsdoelen_Schema,
    Beleidsprestaties_Schema,
    Beleidsregels_Schema,
    Maatregelen_Schema,
    Themas_Schema,
    Werkingsgebieden_Schema,
    Verordeningen_Schema,
]

linker_tables = [
    ("Beleidskeuze_Ambities", "Ambitie_UUID"),
    ("Beleidskeuze_Belangen", "Belang_UUID"),
    ("Beleidskeuze_Beleidsdoelen", "Beleidsdoel_UUID"),
    ("Beleidskeuze_Beleidsprestaties", "Beleidsprestatie_UUID"),
    ("Beleidskeuze_Beleidsregels", "Beleidsregel_UUID"),
    ("Beleidskeuze_Maatregelen", "Maatregel_UUID"),
    ("Beleidskeuze_Themas", "Thema_UUID"),
    ("Beleidskeuze_Verordeningen", "Verordening_UUID"),
    ("Beleidskeuze_Werkingsgebieden", "Werkingsgebied_UUID"),
]


def show_inlined_properties():
    """We use this to help the frontend."""
    for ep in endpoints:
        print(ep.Meta.slug)
        for ref in ep.Meta.references:
            if isinstance(ep.Meta.references[ref], references.UUID_List_Reference):
                print(
                    "\t", ref, f": Lijst naar {ep.Meta.references[ref].their_tablename}"
                )
            if isinstance(ep.Meta.references[ref], references.UUID_Reference):
                print(
                    "\t",
                    ref,
                    f": Enkele naar {ep.Meta.references[ref].target_tablename}",
                )
            if isinstance(ep.Meta.references[ref], references.Reverse_UUID_Reference):
                print(
                    "\t",
                    ref,
                    f": Reverse van {ep.Meta.references[ref].their_tablename}",
                )


def generate_typescript_defs():
    """This generates typescript definitions for the datamodel"""
    result = ""
    schema_list = [*endpoints, Gebruikers_Schema, Short_Beleidskeuze_Schema]
    for ep in schema_list:
        try:
            refs = ep.Meta.references
        except AttributeError:
            refs = {}

        result += f"interface {ep.Meta.slug}: {{ \n"
        for field, type in ep().fields.items():
            result += _field_to_ts(field, type, refs)
        result += "}\n"
    return result


def _field_to_ts(name, field_type, refs):
    field_name = name
    ts_type = None
    if name in refs:
        ref = refs[name]
        if isinstance(ref, references.UUID_List_Reference) or isinstance(
            ref, references.ID_List_Reference
        ):
            ts_type = f"{ref.schema.Meta.slug}[]"
        elif isinstance(ref, references.UUID_Reference):
            ts_type = f"{ref.schema.Meta.slug}"
        elif isinstance(ref, references.Reverse_UUID_Reference) or isinstance(
            ref, references.Reverse_ID_Reference
        ):
            field_name += "?"
            ts_type = f"{ref.schema.Meta.slug}"
    else:
        if isinstance(field_type, MMF.UUID) or isinstance(field_type, MMF.String):
            ts_type = "string"
        elif isinstance(field_type, MMF.Integer):
            ts_type = "number"
        elif isinstance(field_type, MMF.DateTime):
            ts_type = "Date"
        elif isinstance(field_type, MMF.Nested):
            ts_type = "any[]"
        else:
            raise (ValueError(f"Type not found! {type(field_type)}"))
    return f"\t {field_name}: {ts_type}; \n"


def generate_markdown_view():
    """This generates a markdown rendering of the datamodel"""
    result = ""
    schema_list = [*endpoints]
    for ep in schema_list:
        result += f"### {ep.Meta.slug.capitalize()} \n| Veldnaam | Type | Opmerking | Verplicht | \n | --- | --- | --- | --- | \n"
        for field, _type in ep().fields.items():
            validatorstrf = ""
            validators = _type.validate
            if validators:
                for val in validators:
                    try:
                        validatorstrf += f"Geldig: {val.choices},"
                    except AttributeError:
                        try:
                            validatorstrf += f"Niet: {val.iterable},"
                        except AttributeError:
                            validatorstrf += f"HTML Validatie,"

            result += f"|{field} | {type(_type).__name__} | {validatorstrf} | {_type.required} |\n"
        result += "\n"
    return result
