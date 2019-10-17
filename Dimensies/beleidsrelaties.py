import marshmallow as MM
from .dimensie import Dimensie_Schema


class BeleidsRelatie_Schema(Dimensie_Schema):
    Van_Beleidsbeslissing = MM.fields.UUID(required=True)
    Naar_Beleidsbeslissing = MM.fields.UUID(required=True)
    Titel = MM.fields.Str(required=True, search_field="text")
    Omschrijving = MM.fields.Str(missing=None, search_field="text")
    Status = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Open', 'Akkoord', 'NietAkkoord'])])
    Aanvraag_Datum = MM.fields.DateTime(format='iso', required=True)
    Datum_Akkoord = MM.fields.DateTime(format='iso', allow_none=True, missing=None)