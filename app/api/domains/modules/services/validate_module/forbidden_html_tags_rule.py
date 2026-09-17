from bs4 import BeautifulSoup
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module.validate_module_service import (
    ValidateModuleError,
    ValidateModuleObject,
    ValidateModuleRequest,
    ValidateModuleRule,
)
from app.core.services import MainConfig


class ForbiddenHtmlTagsRuleConfig(BaseModel):
    fields: list[str]
    forbidden_html_tags: list[str]


class ForbiddenHtmlTagsRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig):
        self._config: ForbiddenHtmlTagsRuleConfig = main_config.get_as_model(
            "validate_rules.module.forbidden_html_tags",
            ForbiddenHtmlTagsRuleConfig,
        )

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

        for object_table in request.module_objects:
            for field_name in self._config.fields:
                value: str = str(getattr(object_table, field_name, ""))
                maybe_forbidden_tag = self._has_forbidden_tags(value)
                if maybe_forbidden_tag:
                    errors.append(
                        ValidateModuleError(
                            rule="forbidden_html_tags_rule",
                            object=ValidateModuleObject(
                                code=object_table.Code,
                                object_id=object_table.Object_ID,
                                object_type=object_table.Object_Type,
                                title=object_table.Title,
                            ),
                            messages=[f"Forbidden html tag '{maybe_forbidden_tag}' found in '{field_name}'"],
                        )
                    )

        return errors

    def _has_forbidden_tags(self, text: str) -> str | None:
        soup = BeautifulSoup(text, "html.parser")
        for tag in self._config.forbidden_html_tags:
            elements = soup.find_all(tag)
            if elements:
                return tag
        return None
