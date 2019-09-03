import marshmallow as MM
from .dimensie import Dimensie_Schema


class Maatregelen_Schema(Dimensie_Schema):
    Titel = MM.fields.Str(required=True)
    Omschrijving = MM.fields.Str(missing=None)
    Gebied = MM.fields.UUID(missing=None, attribute='fk_Gebied')
    Verplicht_Programma = MM.fields.Str(missing=None, validate= [MM.validate.OneOf(["Ja", "Nee"])])
    Specifiek_Of_Generiek = MM.fields.Str(missing=None, validate= [MM.validate.OneOf(["Gebiedsspecifiek", "Generiek"])])
    Weblink = MM.fields.Str(missing=None)
    Tags = MM.fields.Str(missing=None)