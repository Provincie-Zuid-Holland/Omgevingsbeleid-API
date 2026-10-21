from dso import Thema, ThemaFactory
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module.validate_module_service import (
    ValidateModuleError,
    ValidateModuleObject,
    ValidateModuleRequest,
    ValidateModuleRule,
)
from app.core.services import MainConfig


class ThemasCheckRuleConfig(BaseModel):
    field: str


class ThemasCheckRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig, dso_thema_factory: ThemaFactory):
        self._config: ThemasCheckRuleConfig = main_config.get_as_model(
            "validate_rules.module.themas_check",
            ThemasCheckRuleConfig,
        )
        self._dso_thema_factory: ThemaFactory = dso_thema_factory

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []
        dso_themas: dict[str, Thema] = self._dso_thema_factory.get_all()

        for object_table in request.module_objects:
            if not getattr(object_table, self._config.field):
                continue

            for thema in getattr(object_table, self._config.field):
                dso_thema: Thema | None = dso_themas.get(thema)
                if dso_thema is None:
                    errors.append(
                        ValidateModuleError(
                            rule="themas_check_rule",
                            object=ValidateModuleObject(
                                code=object_table.code,
                                object_id=object_table.object_id,
                                object_type=object_table.object_type,
                                title=object_table.title,
                            ),
                            messages=[f"Thema '{thema}' can't be found in waardelijst"],
                        )
                    )
                elif dso_thema.deprecated:
                    errors.append(
                        ValidateModuleError(
                            rule="themas_check_rule",
                            object=ValidateModuleObject(
                                code=object_table.code,
                                object_id=object_table.object_id,
                                object_type=object_table.object_type,
                                title=object_table.title,
                            ),
                            messages=[f"Thema '{thema}' is deprecated"],
                        )
                    )
        return errors
