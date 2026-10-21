from dso import Thema, ThemaFactory
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)
from app.core.services import MainConfig


class ThemasCheckRuleConfig(BaseModel):
    field: str


class ThemasCheckRule(ValidatePublicationRule):
    def __init__(self, main_config: MainConfig, dso_thema_factory: ThemaFactory):
        self._config: ThemasCheckRuleConfig = main_config.get_as_model(
            "validate_rules.publication.themas_check",
            ThemasCheckRuleConfig,
        )
        self._dso_thema_factory: ThemaFactory = dso_thema_factory

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []
        dso_themas: dict[str, Thema] = self._dso_thema_factory.get_all()

        for object_to_validate in request.input_data.Publication_Data.used_objects:
            if not object_to_validate.get(self._config.field):
                continue
            themas: list[str] = object_to_validate.get(self._config.field)
            for thema in themas:
                dso_thema: Thema | None = dso_themas.get(thema)
                if dso_thema is None:
                    errors.append(
                        ValidatePublicationError(
                            rule="themas_check_rule",
                            object=ValidatePublicationObject(
                                code=object_to_validate.get("code"),
                                object_id=object_to_validate.get("object_id"),
                                object_type=object_to_validate.get("object_type"),
                                title=object_to_validate.get("title"),
                            ),
                            messages=[f"Thema '{thema}' can't be found in waardelijst"],
                        )
                    )
                elif dso_thema.deprecated:
                    errors.append(
                        ValidatePublicationError(
                            rule="themas_check_rule",
                            object=ValidatePublicationObject(
                                code=object_to_validate.get("code"),
                                object_id=object_to_validate.get("object_id"),
                                object_type=object_to_validate.get("object_type"),
                                title=object_to_validate.get("title"),
                            ),
                            messages=[f"Thema '{thema}' is deprecated"],
                        )
                    )
        return errors
