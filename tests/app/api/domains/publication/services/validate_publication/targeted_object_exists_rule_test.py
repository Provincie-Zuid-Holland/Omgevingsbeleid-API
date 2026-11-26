from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication import (
    TargetedObjectExistsRule,
    TargetedObjectExistsRuleConfig,
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
    rule_config: TargetedObjectExistsRuleConfig = TargetedObjectExistsRuleConfig(
        targets={"verplicht_programma": "Target_Codes"}
    )
    config.get_as_model.return_value = rule_config
    rule = TargetedObjectExistsRule(config)

    used_objects = [
        {
            "Object_Type": "maatregel",
            "Object_ID": "10",
            "Code": "maatregel-10",
            "Title": "M10 title",
        },
        {
            "Object_Type": "verplicht_programma",
            "Object_ID": "20",
            "Code": "verplicht-programma-20",
            "Title": "VP20 title",
            "Target_Codes": ["maatregel-10"],
        },
        {
            "Object_Type": "verplicht_programma",
            "Object_ID": "21",
            "Code": "verplicht-programma-21",
            "Title": "VP21 title",
            "Target_Codes": ["maatregel-99999"],
        },
        {
            "Object_Type": "verplicht_programma",
            "Object_ID": "22",
            "Code": "verplicht-programma-22",
            "Title": "VP22 title",
            "Target_Codes": ["maatregel-10", "maatregel-99998", "maatregel-99997"],
        },
        {
            "Object_Type": "verplicht_programma",
            "Object_ID": "23",
            "Code": "verplicht-programma-23",
            "Title": "VP23 title",
            "Target_Codes": None,
        },
        {
            "Object_Type": "ambitie",
            "Object_ID": "30",
            "Code": "ambitie-30",
            "Title": "A30 title",
        },
    ]

    all_object_codes: set[str] = {str(obj.get("Code")) for obj in used_objects}

    request: ValidatePublicationRequest = ValidatePublicationRequest(
        input_data=make_api_act_input_data(
            Publication_Data=make_publication_data(all_objects=used_objects, all_object_codes=all_object_codes)
        ),
        document_type=DocumentType.VISION,
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidatePublicationError] = rule.validate(db=db, request=request)
    assert len(errors) == 2
    assert [{error.object.code: error.messages} for error in errors] == [
        {"verplicht-programma-21": ["Targeted object maatregel-99999 can't be found in publication"]},
        {
            "verplicht-programma-22": [
                "Targeted object maatregel-99998 can't be found in publication",
                "Targeted object maatregel-99997 can't be found in publication",
            ]
        },
    ]
