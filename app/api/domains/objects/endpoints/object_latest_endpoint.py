from typing import Annotated, Optional, Type

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException
from pydantic import BaseModel

from app.api.api_container import ApiContainer
from app.api.domains.objects.object_repository import ObjectRepository
from app.api.endpoint import BaseEndpointContext
from app.core.tables.objects import ObjectsTable


class ObjectLatestEndpointContext(BaseEndpointContext):
    object_type: str
    response_model: Type[BaseModel]


@inject
def view_object_latest_endpoint(
    lineage_id: int,
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
    context: ObjectLatestEndpointContext = Depends(),
):
    maybe_object: Optional[ObjectsTable] = object_repository.get_latest_by_id(
        context.object_type,
        lineage_id,
    )
    if not maybe_object:
        raise HTTPException(status_code=404, detail="lineage_id does not exist")

    result: BaseModel = context.response_model.model_validate(maybe_object)

    # @todo: run events

    return result
