import uuid
from datetime import datetime
from typing import Annotated, List, Optional, Sequence

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased, joinedload, load_only

from app.api.api_container import ApiContainer
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.types import PublicModuleShort, PublicModuleStatusCode
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.core.services.event.event_manager import EventManager
from app.core.tables.modules import ModuleObjectsTable, ModuleTable
from app.core.types import Model


class PublicModuleObjectContextShort(BaseModel):
    Action: str
    Original_Adjust_On: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)


class PublicModuleObjectShort(BaseModel):
    Module_ID: int
    UUID: uuid.UUID
    Object_Type: str
    Object_ID: int
    Code: str
    Description: str

    Modified_Date: datetime
    Title: str

    ModuleObjectContext: Optional[PublicModuleObjectContextShort] = None

    @field_validator("Description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    model_config = ConfigDict(from_attributes=True)


class PublicModuleOverview(BaseModel):
    Module: PublicModuleShort
    Objects: List[PublicModuleObjectShort]


@inject
def get_public_module_overview_endpoint(
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    event_manager: Annotated[EventManager, Depends(Provide[ApiContainer.event_manager])],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
) -> PublicModuleOverview:
    if not module.Current_Status in PublicModuleStatusCode.values():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status for module")

    status_snapshot_date = module.Status.Created_Date
    subq = module_object_repository._build_snapshot_objects_query(module.Module_ID, status_snapshot_date).subquery()
    aliased_subq = aliased(ModuleObjectsTable, subq)
    stmt = (
        select(aliased_subq)
        .filter(subq.c._RowNumber == 1)
        .filter(subq.c.Deleted == False)
        .options(
            load_only(
                aliased_subq.Module_ID,
                aliased_subq.Object_Type,
                aliased_subq.Object_ID,
                aliased_subq.Code,
                aliased_subq.UUID,
                aliased_subq.Modified_Date,
                aliased_subq.Title,
                aliased_subq.Deleted,
            ),
            joinedload(aliased_subq.ModuleObjectContext),
            joinedload(aliased_subq.ObjectStatics),
        )
    )

    rows: Sequence[ModuleObjectsTable] = db.execute(stmt).scalars().all()
    snapshot_objects: List[PublicModuleObjectShort] = [PublicModuleObjectShort.model_validate(r) for r in rows]

    event: RetrievedObjectsEvent = event_manager.dispatch(
        RetrievedObjectsEvent.create(
            snapshot_objects,
            "deprecated",
            Model(
                id="hardcoded_PublicModuleOverview",
                name="PublicModuleOverview",
                pydantic_model=PublicModuleObjectShort,
            ),
        )
    )
    objects: List[PublicModuleObjectShort] = event.payload.rows

    response = PublicModuleOverview(
        Module=PublicModuleShort.model_validate(module),
        Objects=objects,
    )
    return response
