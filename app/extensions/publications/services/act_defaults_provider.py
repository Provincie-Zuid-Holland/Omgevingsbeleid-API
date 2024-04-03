from app.extensions.publications.models import ActMetadata


class ActDefaultsProvider:
    def __init__(self, defaults: dict):
        self._defaults: dict = defaults

    def get_metadata(self, document_type: str, procedure_type: str) -> ActMetadata:
        key: str = f"{procedure_type}_{document_type}"
        defaults: dict = self._defaults[key]["metadata"]
        result: ActMetadata = ActMetadata(**defaults)
        return result
