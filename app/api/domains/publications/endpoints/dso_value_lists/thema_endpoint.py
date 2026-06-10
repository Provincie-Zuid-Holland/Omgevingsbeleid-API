from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from dso import Thema, ThemaFactory
from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from app.api.api_container import ApiContainer


class ListThemaResponse(BaseModel):
    themas: List[Thema]

    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)


@inject
def get_thema_endpoint(
    dso_thema_factory: Annotated[ThemaFactory, Depends(Provide[ApiContainer.dso_thema_factory])],
) -> ListThemaResponse:
    themas = list(dso_thema_factory.get_all().values())
    return ListThemaResponse(themas=themas)
