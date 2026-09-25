import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased, joinedload, load_only

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.types import PublicModuleShort, PublicModuleStatusCode
from app.api.events.event_manager import ApiEventManager
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.core.tables.modules import ModuleObjectsTable, ModuleTable
from app.core.types import Model


class PublicModuleObjectContextShort(BaseModel):
    Action: str
    Original_Adjust_On: uuid.UUID | None = None
    model_config = ConfigDict(from_attributes=True)


class PublicModuleObjectShort(BaseModel):
    module_id: int
    id: uuid.UUID
    object_type: str
    object_id: int
    code: str
    description: str

    modified_date: datetime
    title: str

    module_object_context: PublicModuleObjectContextShort | None = None

    @field_validator("description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    model_config = ConfigDict(from_attributes=True)


class PublicModuleOverview(BaseModel):
    module: PublicModuleShort
    objects: list[PublicModuleObjectShort]


@inject
def get_public_module_overview_endpoint(
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    session: Annotated[Session, Depends(depends_db_session)],
    event_manager: Annotated[ApiEventManager, Depends(Provide[ApiContainer.event_manager])],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
) -> PublicModuleOverview:
    if module.current_status not in PublicModuleStatusCode.values():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status for module")

    status_snapshot_date = module.status.created_date
    subq = module_object_repository._build_snapshot_objects_query(module.module_id, status_snapshot_date).subquery()
    aliased_subq = aliased(ModuleObjectsTable, subq)
    stmt = (
        select(aliased_subq)
        .filter(subq.c._row_number == 1)
        .filter(subq.c.deleted == False)
        .options(
            load_only(
                aliased_subq.module_id,
                aliased_subq.object_type,
                aliased_subq.object_id,
                aliased_subq.code,
                aliased_subq.id,
                aliased_subq.modified_date,
                aliased_subq.Title,
                aliased_subq.deleted,
            ),
            joinedload(aliased_subq.module_object_context),
            joinedload(aliased_subq.object_statics),
        )
    )

    rows: Sequence[ModuleObjectsTable] = session.execute(stmt).scalars().all()
    snapshot_objects: list[PublicModuleObjectShort] = [PublicModuleObjectShort.model_validate(r) for r in rows]

    event: RetrievedObjectsEvent = event_manager.dispatch(
        session,
        RetrievedObjectsEvent.create(
            snapshot_objects,
            "deprecated",
            Model(
                id="hardcoded_PublicModuleOverview",
                name="PublicModuleOverview",
                pydantic_model=PublicModuleObjectShort,
            ),
        ),
    )
    objects: list[PublicModuleObjectShort] = event.payload.rows

    response = PublicModuleOverview(
        module=PublicModuleShort.model_validate(module),
        objects=objects,
    )
    return response
