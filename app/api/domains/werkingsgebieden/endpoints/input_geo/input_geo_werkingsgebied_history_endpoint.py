from datetime import date
from typing import Annotated, List, Optional, Sequence

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.werkingsgebieden.repositories.input_geo_werkingsgebieden_repository import (
    InputGeoWerkingsgebiedenRepository,
)
from app.api.domains.werkingsgebieden.types import InputGeoWerkingsgebied
from app.core.tables.werkingsgebieden import InputGeoWerkingsgebiedenTable


@inject
def get_input_geo_werkingsgebieden_history_endpoint(
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        InputGeoWerkingsgebiedenRepository, Depends(Provide[ApiContainer.input_geo_werkingsgebieden_repository])
    ],
    title: str,
    from_date: Optional[date] = None,
) -> List[InputGeoWerkingsgebied]:
    werkingsgebieden: Sequence[InputGeoWerkingsgebiedenTable] = repository.get_by_title_paginated(
        session, title, from_date
    )
    result: List[InputGeoWerkingsgebied] = [InputGeoWerkingsgebied.model_validate(w) for w in werkingsgebieden]

    return result
