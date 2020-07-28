import marshmallow as MM
from .dimensie import Dimensie_Schema


class BeleidsRelatie_Schema(Dimensie_Schema):
    Van_Beleidsbeslissing = MM.fields.UUID(required=True, obprops=[])
    Naar_Beleidsbeslissing = MM.fields.UUID(required=True, obprops=[])
    Titel = MM.fields.Str(required=True, obprops=['search_field'])
    Omschrijving = MM.fields.Str(missing=None, obprops=['search_field'])
    Status = MM.fields.Str(required=True, validate=[MM.validate.OneOf(['Open', 'Akkoord', 'NietAkkoord', 'Verbroken'])], obprops=[])
    Aanvraag_Datum = MM.fields.DateTime(format='iso', required=True, obprops=[])
    Datum_Akkoord = MM.fields.DateTime(format='iso', allow_none=True, missing=None, obprops=[])