from typing import Annotated, Type

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.endpoint import BaseEndpointContext


class ObjectLatestEndpointContext(BaseEndpointContext):
    response_model: Type[BaseModel]


@inject
def view_object_latest_endpoint(
    lineage_id: int,
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    context: ObjectLatestEndpointContext = Depends(),
):
    result: BaseModel = context.response_model.model_validate({})
    return result
