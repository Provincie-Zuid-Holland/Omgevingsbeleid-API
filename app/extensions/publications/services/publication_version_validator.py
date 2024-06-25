from typing import List

from pydantic import ValidationError

from app.extensions.publications.enums import ProcedureType
from app.extensions.publications.models.models import PublicationVersionDraftValidated, PublicationVersionFinalValidated
from app.extensions.publications.tables.tables import PublicationVersionTable


class PublicationVersionValidator:
    def get_errors(self, publication_version: PublicationVersionTable) -> List[dict]:
        try:
            if publication_version.Publication.Procedure_Type == ProcedureType.DRAFT.value:
                _ = PublicationVersionDraftValidated.from_orm(publication_version)
            else:
                _ = PublicationVersionFinalValidated.from_orm(publication_version)

            return []
        except ValidationError as e:
            return e.errors()
