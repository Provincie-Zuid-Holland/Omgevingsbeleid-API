from typing import Any
from unittest.mock import Mock

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.services.validate_publication import (
    RequiredObjectFieldsRule,
    ValidatePublicationError,
    ValidatePublicationRequest,
)
from app.api.domains.publications.types.enums import DocumentType
from app.api.services.async_model_validators_service import AsyncModelValidatorsService
from tests.app.api.domains.publications.services.validate_publication.type_factories import (
    make_api_act_input_data,
    make_publication_data,
)


class Ambitie(BaseModel):
    title: str = Field(..., min_length=5)

    model_config = ConfigDict(from_attributes=True)


async def test_validate():
    document_type_map = {
        "omgevingsvisie": {
            "ambitie": Ambitie,
        }
    }
    used_objects: list[dict[str, Any]] = [
        {
            "object_type": "ambitie",
            "object_id": "1",
            "code": "ambitie-1",
            "title": "Obj",  # Title too short
        },
        {
            "object_type": "ambitie",
            "object_id": "2",
            "code": "ambitie-2",
            "title": "Object valid",
        },
        {
            "object_type": "beleidsdoel",  # Object type not in map, so skipped
            "object_id": "1",
            "code": "beleidsdoel-1",
            "title": "Obj",
        },
    ]
    rule = RequiredObjectFieldsRule(document_type_map, AsyncModelValidatorsService())
    request: ValidatePublicationRequest = ValidatePublicationRequest(
        input_data=make_api_act_input_data(publication_data=make_publication_data(used_objects=used_objects)),
        document_type=DocumentType.VISION,
    )
    db: Mock | AsyncSession = Mock(AsyncSession)
    errors: list[ValidatePublicationError] = await rule.validate(db=db, request=request)
    assert len(errors) == 1
    assert [error.object.code for error in errors] == [
        "ambitie-1",
    ]
