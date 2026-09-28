from unittest.mock import Mock

from dso import Thema, ThemaFactory
from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication import (
    ThemasCheckRule,
    ThemasCheckRuleConfig,
)
from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationRequest,
)
from app.api.domains.publications.types.enums import DocumentType
from app.core.services import MainConfig
from tests.app.api.domains.publication.services.validate_publication.type_factories import (
    make_api_act_input_data,
    make_publication_data,
)


def test_validate():
    config: Mock | MainConfig = Mock(MainConfig)
    rule_config: ThemasCheckRuleConfig = ThemasCheckRuleConfig(field="themas")
    config.get_as_model.return_value = rule_config

    def _get_thema(label: str, deprecated: bool) -> Thema:
        return Thema(
            label=label,
            deprecated=deprecated,
            term="term",
            uri="http://some-uri",
            definitie="definitie",
            toelichting="toelichting",
            bron="bron",
            domein="domein",
        )

    factory: Mock | ThemaFactory = Mock(ThemaFactory)
    factory.get_all.return_value = {
        "thema-1": _get_thema(label="thema-1", deprecated=False),
        "thema-2": _get_thema(label="thema-2", deprecated=True),
        "thema-3": _get_thema(label="thema-2", deprecated=False),
    }

    rule: ThemasCheckRule = ThemasCheckRule(config, factory)
    used_objects = [
        {
            "object_type": "ambitie",  # No themas
            "object_id": "1",
            "code": "ambitie-1",
            "title": "A1 title",
        },
        {
            "object_type": "ambitie",
            "object_id": "2",
            "code": "ambitie-2",
            "title": "A2 title",
            "themas": ["thema-1"],
        },
        {
            "object_type": "ambitie",
            "object_id": "3",
            "code": "ambitie-3",
            "title": "A3 title",
            "themas": ["thema-2"],  # deprecated
        },
        {
            "object_type": "ambitie",
            "object_id": "4",
            "code": "ambitie-4",
            "title": "A4 title",
            "themas": ["thema-unknown"],  # non-existing
        },
        {
            "object_type": "ambitie",
            "object_id": "5",
            "code": "ambitie-5",
            "title": "A5 title",
            "themas": ["thema-1", "thema-2"],  # one valid, one deprecated
        },
        {
            "object_type": "ambitie",
            "object_id": "6",
            "code": "ambitie-6",
            "title": "A6 title",
            "themas": ["thema-1", "thema-unknown"],  # one valid, one non-existing
        },
        {
            "object_type": "ambitie",
            "object_id": "7",
            "code": "ambitie-7",
            "title": "A7 title",
            "themas": ["thema-1", "thema-3"],  # multiple valid
        },
    ]
    request: ValidatePublicationRequest = ValidatePublicationRequest(
        input_data=make_api_act_input_data(Publication_Data=make_publication_data(used_objects=used_objects)),
        document_type=DocumentType.VISION,
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidatePublicationError] = rule.validate(db=db, request=request)
    assert len(errors) == 4
    assert [error.object.code for error in errors] == ["ambitie-3", "ambitie-4", "ambitie-5", "ambitie-6"]
