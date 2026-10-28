from typing import Any
from unittest.mock import Mock

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.domains.publications.services.validate_publication import (
    RequiredObjectFieldsRule,
    ValidatePublicationError,
    ValidatePublicationRequest,
)
from app.api.domains.publications.types.enums import DocumentType
from tests.app.api.domains.publication.services.validate_publication.type_factories import (
    make_api_act_input_data,
    make_publication_data,
)


class Ambitie(BaseModel):
    Title: str = Field(..., min_length=5)

    model_config = ConfigDict(from_attributes=True)


def test_validate():
    document_type_map = {
        "omgevingsvisie": {
            "ambitie": Ambitie,
        }
    }
    used_objects: list[dict[str, Any]] = [
        {
            "Object_Type": "ambitie",
            "Object_ID": "1",
            "Code": "ambitie-1",
            "Title": "Obj",  # Title too short
        },
        {
            "Object_Type": "ambitie",
            "Object_ID": "2",
            "Code": "ambitie-2",
            "Title": "Object valid",
        },
        {
            "Object_Type": "beleidsdoel",  # Object type not in map, so skipped
            "Object_ID": "1",
            "Code": "beleidsdoel-1",
            "Title": "Obj",
        },
    ]
    rule = RequiredObjectFieldsRule(document_type_map=document_type_map)
    request: ValidatePublicationRequest = ValidatePublicationRequest(
        input_data=make_api_act_input_data(Publication_Data=make_publication_data(used_objects=used_objects)),
        document_type=DocumentType.VISION,
    )
    db: Mock | Session = Mock(Session)
    errors: list[ValidatePublicationError] = rule.validate(db=db, request=request)
    assert len(errors) == 1
    assert [error.object.code for error in errors] == [
        "ambitie-1",
    ]
