from app.extensions.publications.models import BillCompact, BillMetadata, Procedural


class PublicationVersionDefaultsProvider:
    def __init__(self, defaults: dict):
        self._defaults: dict = defaults

    def get_bill_metadata(self, document_type: str) -> BillMetadata:
        defaults: dict = self._defaults[document_type.lower()]["bill_metadata"]
        result: BillMetadata = BillMetadata(**defaults)
        return result

    def get_bill_compact(self, document_type: str) -> BillCompact:
        defaults: dict = self._defaults[document_type.lower()]["bill_compact"]
        result: BillCompact = BillCompact(**defaults)
        return result

    def get_procedural(self) -> Procedural:
        result: Procedural = Procedural()
        return result
