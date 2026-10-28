from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)


class GebiedengroepHasGiosRule(ValidatePublicationRule):
    async def validate(self, db: AsyncSession, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        for gebiedengroep in request.input_data.publication_data.gebiedengroepen.values():
            if not gebiedengroep.gio_key:
                errors.append(
                    ValidatePublicationError(
                        rule="gebiedengroep_has_no_gio",
                        object=ValidatePublicationObject(
                            code=gebiedengroep.code,
                            title=gebiedengroep.title,
                        ),
                        messages=[f"Gebiedengroep code '{gebiedengroep.code}' has no valid gio"],
                    )
                )

        return errors
