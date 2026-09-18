from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.others.repositories.hoofdlijn_repository import HoofdlijnRepository
from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)
from app.core.services import MainConfig


@dataclass
class HoofdlijnenCheckRuleData:
    hoofdlijnen_uuids: set[UUID]
    object_to_validate: dict


class HoofdlijnenCheckRuleConfig(BaseModel):
    field: str
    allowed_object_types: list[str]


class HoofdlijnenCheckRule(ValidatePublicationRule):
    def __init__(self, main_config: MainConfig, hoofdlijn_repository: HoofdlijnRepository):
        self._config: HoofdlijnenCheckRuleConfig = main_config.get_as_model(
            "validate_rules.publication.hoofdlijnen_check",
            HoofdlijnenCheckRuleConfig,
        )
        self._hoofdlijn_repository: HoofdlijnRepository = hoofdlijn_repository

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        object_data: list[HoofdlijnenCheckRuleData] = []
        hoofdlijnen_set: set[UUID] = set()

        errors: list[ValidatePublicationError] = []
        for object_to_validate in request.input_data.Publication_Data.used_objects:
            if object_to_validate.get("Object_Type") not in self._config.allowed_object_types:
                continue

            field_value: list[str] | None = object_to_validate.get(self._config.field)
            if not field_value:
                continue

            hoofdlijnen_uuids: set[UUID] = {UUID(hoofdlijn_uuid) for hoofdlijn_uuid in field_value}
            object_data.append(
                HoofdlijnenCheckRuleData(hoofdlijnen_uuids=hoofdlijnen_uuids, object_to_validate=object_to_validate)
            )
            hoofdlijnen_set.update(hoofdlijnen_uuids)

        if not hoofdlijnen_set:
            return errors

        found_hoofdlijnen_uuids: set[UUID] = self._hoofdlijn_repository.get_existing_uuids(db, hoofdlijnen_set)
        missing_uuids = hoofdlijnen_set - found_hoofdlijnen_uuids
        if not missing_uuids:
            return errors

        for data in object_data:
            missing_for_object: set[UUID] = data.hoofdlijnen_uuids & missing_uuids
            if missing_for_object:
                missing_displayed: list[str] = sorted(str(uuidx) for uuidx in missing_for_object)
                errors.append(
                    ValidatePublicationError(
                        rule="hoofdlijnen_check_rule",
                        object=ValidatePublicationObject(
                            code=data.object_to_validate.get("Code"),
                            object_id=data.object_to_validate.get("Object_ID"),
                            object_type=data.object_to_validate.get("Object_Type"),
                            title=data.object_to_validate.get("Title"),
                        ),
                        messages=[f"Hoofdlijnen with IDs {', '.join(missing_displayed)} are unknown"],
                    )
                )
        return errors
