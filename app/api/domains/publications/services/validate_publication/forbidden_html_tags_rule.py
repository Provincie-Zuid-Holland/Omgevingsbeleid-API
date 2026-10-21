from bs4 import BeautifulSoup
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)
from app.core.services import MainConfig


class ForbiddenHtmlTagsRuleConfig(BaseModel):
    fields: list[str]
    forbidden_html_tags: list[str]


class ForbiddenHtmlTagsRule(ValidatePublicationRule):
    def __init__(self, main_config: MainConfig):
        self._config: ForbiddenHtmlTagsRuleConfig = main_config.get_as_model(
            "validate_rules.publication.forbidden_html_tags",
            ForbiddenHtmlTagsRuleConfig,
        )

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        for used_object in request.input_data.Publication_Data.used_objects:
            for field_name in self._config.fields:
                value: str = str(used_object.get(field_name, ""))
                maybe_forbidden_tag = self._has_forbidden_tags(value)
                if maybe_forbidden_tag:
                    errors.append(
                        ValidatePublicationError(
                            rule="forbidden_html_tags_rule",
                            object=ValidatePublicationObject(
                                code=used_object.get("code"),
                                object_id=used_object.get("object_id"),
                                object_type=used_object.get("object_type"),
                                title=used_object.get("title"),
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
