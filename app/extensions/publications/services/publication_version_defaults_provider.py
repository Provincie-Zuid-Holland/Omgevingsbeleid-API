from app.extensions.publications.models import BillCompact, BillMetadata, Procedural


class PublicationVersionDefaultsProvider:
    def __init__(self, defaults: dict):
        self._defaults: dict = defaults

    def get_bill_metadata(self, document_type: str, procedure_type: str) -> BillMetadata:
        key: str = self._get_key(document_type, procedure_type)
        defaults: dict = self._defaults[key]["bill_metadata"]
        result: BillMetadata = BillMetadata(**defaults)
        return result

    def get_bill_compact(self, document_type: str, procedure_type: str) -> BillCompact:
        key: str = self._get_key(document_type, procedure_type)
        defaults: dict = self._defaults[key]["bill_compact"]
        result: BillCompact = BillCompact(**defaults)
        return result

    def get_procedural(self) -> Procedural:
        result: Procedural = Procedural()
        return result

    def _get_key(self, document_type: str, procedure_type: str) -> str:
        key: str = f"{procedure_type}_{document_type}".lower()
        return key
