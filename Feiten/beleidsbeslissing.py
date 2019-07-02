import marshmallow as MM
from .feit import Feiten_Schema

class Beleidsbeslissingen_Schema(Feiten_Schema):
    
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