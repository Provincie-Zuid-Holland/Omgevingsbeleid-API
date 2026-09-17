from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.gio import generate_dso_gio_name
from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)
from app.api.domains.publications.types.api_input_data import PublicationGio


class GioDuplicateFilenameRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []
        gios: dict[str, PublicationGio] = {}

        for publication_gio in request.input_data.Publication_Data.gios.values():
            dso_name: str = generate_dso_gio_name(publication_gio.title)
            if dso_name in gios:
                duplicate_gio: PublicationGio = gios.get(dso_name)
                errors.append(
                    ValidatePublicationError(
                        rule="gio_duplicate_filename_rule",
                        object=ValidatePublicationObject(),
                        messages=[
                            f"GIO's [{publication_gio.key}, {duplicate_gio.key}] will generate the same name: '{dso_name}'"
                        ],
                    )
                )
            else:
                gios[dso_name] = publication_gio
        return errors
