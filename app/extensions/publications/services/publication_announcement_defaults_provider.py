from app.extensions.publications.models.models import AnnouncementContent, AnnouncementMetadata, AnnouncementProcedural


class PublicationAnnouncementDefaultsProvider:
    def __init__(self, defaults: dict):
        self._defaults: dict = defaults

    def get_metadata(self, document_type: str, procedure_type: str) -> AnnouncementMetadata:
        key: str = self._get_key(document_type, procedure_type)
        defaults: dict = self._defaults[key]["metadata"]
        result: AnnouncementMetadata = AnnouncementMetadata(**defaults)
        return result

    def get_procedural(self) -> AnnouncementProcedural:
        result: AnnouncementProcedural = AnnouncementProcedural()
        return result

    def get_content(self, document_type: str, procedure_type: str) -> AnnouncementContent:
        key: str = self._get_key(document_type, procedure_type)
        defaults: dict = self._defaults[key]["contents"]
        result: AnnouncementContent = AnnouncementContent(**defaults)
        return result

    def _get_key(self, document_type: str, procedure_type: str) -> str:
        key: str = f"{procedure_type}_{document_type}".lower()
        return key
