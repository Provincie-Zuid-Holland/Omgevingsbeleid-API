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
    rule_config: ThemasCheckRuleConfig = ThemasCheckRuleConfig(field="Themas")
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
            "Object_Type": "ambitie",  # No themas
            "Object_ID": "1",
            "Code": "ambitie-1",
            "Title": "A1 title",
        },
        {
            "Object_Type": "ambitie",
            "Object_ID": "2",
            "Code": "ambitie-2",
            "Title": "A2 title",
            "Themas": ["thema-1"],
        },
        {
            "Object_Type": "ambitie",
            "Object_ID": "3",
            "Code": "ambitie-3",
            "Title": "A3 title",
            "Themas": ["thema-2"],  # deprecated
        },
        {
            "Object_Type": "ambitie",
            "Object_ID": "4",
            "Code": "ambitie-4",
            "Title": "A4 title",
            "Themas": ["thema-unknown"],  # non-existing
        },
        {
            "Object_Type": "ambitie",
            "Object_ID": "5",
            "Code": "ambitie-5",
            "Title": "A5 title",
            "Themas": ["thema-1", "thema-2"],  # one valid, one deprecated
        },
        {
            "Object_Type": "ambitie",
            "Object_ID": "6",
            "Code": "ambitie-6",
            "Title": "A6 title",
            "Themas": ["thema-1", "thema-unknown"],  # one valid, one non-existing
        },
        {
            "Object_Type": "ambitie",
            "Object_ID": "7",
            "Code": "ambitie-7",
            "Title": "A7 title",
            "Themas": ["thema-1", "thema-3"],  # multiple valid
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
