from typing import Annotated, List

from dependency_injector.wiring import inject, Provide
from dso import GebiedsaanwijzingenFactory, Gebiedsaanwijzingen
from dso.models import DocumentType
from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing
from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from app.api.api_container import ApiContainer


class ListAreaDesignationResponse(BaseModel):
    gebiedsaanwijzingen: List[Gebiedsaanwijzing]

    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)


@inject
def get_area_designation_endpoint(
    dso_gebiedsaanwijzingen_factory: Annotated[
        GebiedsaanwijzingenFactory, Depends(Provide[ApiContainer.dso_gebiedsaanwijzingen_factory])
    ],
) -> ListAreaDesignationResponse:
    gebiedsaanwijzingen_programma: Gebiedsaanwijzingen = dso_gebiedsaanwijzingen_factory.get_for_document(
        DocumentType.PROGRAMMA
    )
    return ListAreaDesignationResponse(gebiedsaanwijzingen=gebiedsaanwijzingen_programma._data)
