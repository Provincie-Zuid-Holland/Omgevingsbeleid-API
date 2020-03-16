import marshmallow as MM
from .dimensie import Dimensie_Schema


class Maatregelen_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Gebied = MM.fields.UUID(missing=None, attribute='fk_Gebied', obprops=[])
    Verplicht_Programma = MM.fields.Str(missing=None, validate= [MM.validate.OneOf(["Ja", "Nee"])], obprops=[])
    Specifiek_Of_Generiek = MM.fields.Str(missing=None, validate= [MM.validate.OneOf(["Gebiedsspecifiek", "Generiek"])], obprops=[])
    Weblink = MM.fields.Str(missing=None, obprops=[])
    Tags = MM.fields.Str(missing=None, obprops=[])