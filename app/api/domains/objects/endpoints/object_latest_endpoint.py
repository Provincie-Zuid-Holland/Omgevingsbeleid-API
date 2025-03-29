from typing import Type
from dependency_injector.wiring import inject, Provide
from fastapi import Depends
from fastapi.responses import JSONResponse

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.endpoint import BaseEndpointContext


class ObjectLatestEndpointContext(BaseEndpointContext):
    # response_config_model: Model
    response_type: Type[BaseModel]


@inject
async def view_endpoint(
    lineage_id: int,
    db: Session = Depends(Provide[ApiContainer.db]),
    context: ObjectLatestEndpointContext = Depends(),
) -> JSONResponse:
    return JSONResponse(content={})
