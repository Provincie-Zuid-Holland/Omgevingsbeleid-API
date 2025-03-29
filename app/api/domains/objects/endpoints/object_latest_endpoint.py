from re import A
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


def view_endpoint(context: ObjectLatestEndpointContext):
    @inject
    def entry(
        lineage_id: int,
        db: Session = Depends(Provide[ApiContainer.db]),
    ) -> JSONResponse:
        # content not important for this example
        print(str(context.response_type))
        return JSONResponse(content={})

    return entry


@inject
async def view_endpoint2(
    lineage_id: int,
    db: Session = Depends(Provide[ApiContainer.db]),
    context: ObjectLatestEndpointContext = Depends(),
) -> JSONResponse:
    # content not important for this example
    print(str(context.response_type))
    return JSONResponse(content={})

