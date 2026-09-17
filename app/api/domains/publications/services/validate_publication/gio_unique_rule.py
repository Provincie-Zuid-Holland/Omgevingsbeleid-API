from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.gio import generate_dso_gio_name
from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)
from app.api.domains.publications.types.api_input_data import PublicationGio


class GioUniqueRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []
        gios: dict[str, PublicationGio] = {}

        for publication_gio in request.input_data.Publication_Data.gios.values():
            dso_name: str = generate_dso_gio_name(publication_gio.title)
            if dso_name in gios:
                existing_gio = gios.get(dso_name)
                if publication_gio.source_codes == existing_gio.source_codes:
                    errors.append(
                        ValidatePublicationError(
                            rule="gio_unique_rule",
                            object=ValidatePublicationObject(),
                            messages=[
                                f"GIO's [{publication_gio.key}, {existing_gio.key}] have the same title '{dso_name}' and source codes {existing_gio.source_codes}"
                            ],
                        )
                    )
            else:
                gios.update({dso_name: publication_gio})
        return errors
