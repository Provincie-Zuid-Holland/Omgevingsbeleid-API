from typing import Annotated, List

from dso.services.ow.imow_waardelijsten import NON_ALLOWED_DOCUMENT_TYPE_MAPPING
from dso.services.ow.imow_waardelijsten import TypeGebiedsaanwijzingEnum as AreaDesignationTypes
from fastapi import Depends
from pydantic import BaseModel

from app.api.domains.publications.types.enums import DocumentType


class AreaDesignationValueList(BaseModel):
    Allowed_Values: List[str]


async def get_area_designation_types_endpoint(
    document_type: Annotated[DocumentType, Depends()],
) -> AreaDesignationValueList:
    non_allowed: List[AreaDesignationTypes] = NON_ALLOWED_DOCUMENT_TYPE_MAPPING.get(document_type, [])
    allowed_types_list: List[str] = [e.name for e in AreaDesignationTypes if e not in non_allowed]
    return AreaDesignationValueList(Allowed_Values=allowed_types_list)
