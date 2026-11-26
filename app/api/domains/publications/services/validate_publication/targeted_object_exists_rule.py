from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)
from app.core.services import MainConfig


class TargetedObjectExistsRuleConfig(BaseModel):
    targets: dict[str, str]


class TargetedObjectExistsRule(ValidatePublicationRule):
    def __init__(self, main_config: MainConfig):
        self._config: TargetedObjectExistsRuleConfig = main_config.get_as_model(
            "validate_rules.publication.targeted_object_exists",
            TargetedObjectExistsRuleConfig,
        )

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        for object_current in request.input_data.Publication_Data.all_objects:
            field: str | None = self._config.targets.get(object_current.get("Object_Type"))
            if not field:
                continue

            target_codes: list[str] = object_current.get(field) or []
            missing_codes: list[str] = [
                code for code in target_codes if code not in request.input_data.Publication_Data.all_object_codes
            ]
            if not missing_codes:
                continue

            errors.append(
                ValidatePublicationError(
                    rule="targeted_object_exists_rule",
                    object=ValidatePublicationObject(
                        code=object_current.get("Code"),
                        object_id=object_current.get("Object_ID"),
                        object_type=object_current.get("Object_Type"),
                        title=object_current.get("Title", ""),
                    ),
                    messages=[f"Targeted object {code} can't be found in publication" for code in missing_codes],
                )
            )
        return errors
