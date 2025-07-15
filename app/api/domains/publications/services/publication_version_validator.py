from typing import List

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from app.api.domains.publications.types.enums import ProcedureType
from app.api.domains.publications.types.models import PublicationVersionDraftValidated, PublicationVersionFinalValidated
from app.core.tables.publications import PublicationVersionTable


class PublicationVersionValidator:
    def get_errors(self, publication_version: PublicationVersionTable) -> List[ErrorDetails]:
        try:
            if publication_version.Publication.Procedure_Type == ProcedureType.DRAFT.value:
                _ = PublicationVersionDraftValidated.model_validate(publication_version)
            else:
                _ = PublicationVersionFinalValidated.model_validate(publication_version)

            return []
        except ValidationError as e:
            return e.errors()
