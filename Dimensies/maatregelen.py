import marshmallow as MM
from .dimensie import Dimensie_Schema
from lxml import html
from globals import min_datetime, max_datetime


class Maatregelen_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    # Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Toelichting = MM.fields.Str(missing=None, obprops=['search_field'])
    Toelichting_Raw = MM.fields.Method(missing=None, obprops=[])
    Gebied = MM.fields.UUID(
        missing=None, attribute='fk_Gebied', obprops=['geo_field'])
    Gebied_Duiding = MM.fields.Str(allow_none=True, missing="Indicatief", validate=[
                                   MM.validate.OneOf(["Indicatief", "Exact"])], obprops=[])
    # Verplicht_Programma = MM.fields.Str(missing=None, validate= [MM.validate.OneOf(["Ja", "Nee"])], obprops=[])
    # Specifiek_Of_Generiek = MM.fields.Str(missing=None, validate= [MM.validate.OneOf(["Gebiedsspecifiek", "Generiek"])], obprops=[])
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Tags = MM.fields.Str(missing=None, obprops=[])
    Status = MM.fields.Str(required=True, validate=[MM.validate.OneOf([
        "Definitief ontwerp GS", "Definitief ontwerp GS concept", "Definitief ontwerp PS", "Niet-Actief", "Ontwerp GS", "Ontwerp GS Concept", "Ontwerp in inspraak", "Ontwerp PS", "Uitgecheckt", "Vastgesteld", "Vigerend", "Vigerend gearchiveerd"])], obprops=[])
    Begin_Geldigheid = MM.fields.DateTime(format='iso', missing=min_datetime, allow_none=True, obprops=[])
    Eind_Geldigheid = MM.fields.DateTime(format='iso', missing=max_datetime, allow_none=True, obprops=[])

    @MM.post_load
    def toelichting_to_raw(self, data, **kwargs):
        data['Toelichting_Raw'] = str(
            html.fromstring(data['Toelichting']).text_content())
        return data
