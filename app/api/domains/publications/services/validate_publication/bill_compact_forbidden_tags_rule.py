from typing import Any

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


class BillCompactForbiddenTagsRuleConfig(BaseModel):
    fields: list[str]
    forbidden_tags: list[str]


class BillCompactForbiddenTagsRule(ValidatePublicationRule):
    def __init__(self, main_config: MainConfig):
        self._config: BillCompactForbiddenTagsRuleConfig = main_config.get_as_model(
            "validate_rules.publication.bill_compact_forbidden_tags",
            BillCompactForbiddenTagsRuleConfig,
        )

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        bill_compact: dict[str, Any] = request.input_data.Publication_Version.bill_compact or {}
        for article_field in self._config.fields:
            article: str | None = bill_compact.get(article_field, None)
            if not article:
                continue

            soup = BeautifulSoup(article, "html.parser")
            for tag in self._config.forbidden_tags:
                tags = soup.find_all(tag)
                if len(tags) == 0:
                    continue
                errors.append(
                    ValidatePublicationError(
                        rule="bill_compact_forbidden_tags_rule",
                        object=ValidatePublicationObject(),
                        messages=[
                            f"Bill compact field {article_field} contains at least one forbidden tag: {tag.capitalize()}"
                        ],
                    )
                )
        return errors
