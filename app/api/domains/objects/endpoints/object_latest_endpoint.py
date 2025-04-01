from typing import Type

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.endpoint import BaseEndpointContext
from app.container import Container


class ObjectLatestEndpointContext(BaseEndpointContext):
    # response_config_model: Model
    response_type: Type[BaseModel]


@inject
async def view_object_latest_endpoint(
    lineage_id: int,
    db: Session = Depends(Provide[Container.db]),
    context: ObjectLatestEndpointContext = Depends(),
) -> JSONResponse:
    return JSONResponse(content={})
