from bs4 import BeautifulSoup, ResultSet, Tag
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)


class UsedObjectTypeExistsRule(ValidatePublicationRule):
    async def validate(self, db: AsyncSession, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []
        soup: BeautifulSoup = BeautifulSoup(request.input_data.publication_data.parsed_template, "html.parser")
        object_tags: ResultSet[Tag] = soup.find_all("object")
        objects: list[str] = [obj.get("code") for obj in object_tags if obj.get("code")]
        object_types: set[str] = {v.split("-", 1)[0] for v in objects}
        object_templates: set[str] = request.input_data.publication_version.publication.template.object_templates.keys()

        for object_type in object_types:
            if object_type not in object_templates:
                errors.append(
                    ValidatePublicationError(
                        rule="used_object_type_exists_rule",
                        object=ValidatePublicationObject(
                            object_type=object_type,
                        ),
                        messages=[f"Object type '{object_type}' used in object template can't be found in publication"],
                    )
                )
        return errors
