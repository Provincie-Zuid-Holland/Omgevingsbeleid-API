from typing import Annotated

from dependency_injector.wiring import Provide, inject
from dso import Gebiedsaanwijzingen, GebiedsaanwijzingenFactory
from dso.models import DocumentType
from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing
from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from app.api.api_container import ApiContainer


class ListAreaDesignationResponse(BaseModel):
    gebiedsaanwijzingen: list[Gebiedsaanwijzing]

    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)


@inject
def get_area_designation_endpoint(
    dso_gebiedsaanwijzingen_factory: Annotated[
        GebiedsaanwijzingenFactory, Depends(Provide[ApiContainer.dso_gebiedsaanwijzingen_factory])
    ],
) -> ListAreaDesignationResponse:
    gebiedsaanwijzingen_programma: Gebiedsaanwijzingen | None = dso_gebiedsaanwijzingen_factory.get_for_document(
        DocumentType.PROGRAMMA
    )
    gebiedsaanwijzingen_list: list[Gebiedsaanwijzing] = []
    if gebiedsaanwijzingen_programma is not None:
        gebiedsaanwijzingen_list = gebiedsaanwijzingen_programma.get_list()
    return ListAreaDesignationResponse(gebiedsaanwijzingen=gebiedsaanwijzingen_list)
