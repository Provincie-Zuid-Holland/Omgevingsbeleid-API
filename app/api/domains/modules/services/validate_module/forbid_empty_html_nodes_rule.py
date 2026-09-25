from bs4 import BeautifulSoup, PageElement, Tag
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.domains.modules.services.validate_module.validate_module_service import (
    ValidateModuleError,
    ValidateModuleObject,
    ValidateModuleRequest,
    ValidateModuleRule,
)
from app.core.services import MainConfig


class ForbidEmptyHtmlNodesRuleConfig(BaseModel):
    fields: list[str]
    html_void_elements: list[str] = Field(default_factory=list)
    allowed_empty_when_sole_child: dict[str, list[str]] = Field(default_factory=dict)


class ForbidEmptyHtmlNodesRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig):
        self._config: ForbidEmptyHtmlNodesRuleConfig = main_config.get_as_model(
            "validate_rules.module.forbid_empty_html_nodes",
            ForbidEmptyHtmlNodesRuleConfig,
        )

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

        for object_table in request.module_objects:
            for field_name in self._config.fields:
                value: str = str(getattr(object_table, field_name, ""))
                if self._has_empty_nodes(value):
                    errors.append(
                        ValidateModuleError(
                            rule="forbid_empty_html_nodes_rule",
                            object=ValidateModuleObject(
                                code=object_table.code,
                                object_id=object_table.object_id,
                                object_type=object_table.object_type,
                                title=object_table.title,
                            ),
                            messages=[f"Empty html node found in '{field_name}' for object {object_table.code}"],
                        )
                    )

        return errors

    def _has_empty_nodes(self, text: str) -> bool:
        soup: BeautifulSoup = BeautifulSoup(text, "html.parser")

        for tag in soup.find_all(True):
            if tag.name in self._config.html_void_elements:
                continue
            if tag.get_text(strip=True):
                continue
            if any(child.name for child in tag.children):
                continue
            if self._is_allowed_empty_sole_child(tag):
                continue
            return True

        return False

    def _is_allowed_empty_sole_child(self, tag: Tag) -> bool:
        parent: Tag | None = tag.parent
        if parent is None:  # practically unreachable when using _has_empty_nodes
            return False

        allowed_children: list[str] = self._config.allowed_empty_when_sole_child.get(parent.name, [])
        if tag.name not in allowed_children:
            return False

        # Only allowed when this empty tag is the single element child and the parent holds no other text,
        # so `<td><p></p></td>` passes but `<td><p>text</p><p></p></td>` does not.
        element_children: list[PageElement] = [child for child in parent.children if child.name]
        if len(element_children) != 1:
            return False
        return not parent.get_text(strip=True)
