import uuid
from datetime import datetime
from typing import Annotated, List, Optional, Sequence

from fastapi import Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, aliased, joinedload, load_only

from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.types import Module as ModuleClass
from app.api.domains.modules.types import ModuleStatus
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.modules import ModuleObjectsTable, ModuleTable
from app.core.tables.users import UsersTable


class ObjectStaticShort(BaseModel):
    Owner_1_UUID: Optional[uuid.UUID] = None
    Owner_2_UUID: Optional[uuid.UUID] = None
    Portfolio_Holder_1_UUID: Optional[uuid.UUID] = None
    Portfolio_Holder_2_UUID: Optional[uuid.UUID] = None
    Client_1_UUID: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)


class ModuleObjectContextShort(BaseModel):
    Action: str
    Original_Adjust_On: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)


class ModuleObjectShort(BaseModel):
    Module_ID: int
    Object_Type: str
    Object_ID: int
    Code: str
    UUID: uuid.UUID

    Modified_Date: datetime
    Title: str

    ObjectStatics: Optional[ObjectStaticShort] = None
    ModuleObjectContext: Optional[ModuleObjectContextShort] = None
    model_config = ConfigDict(from_attributes=True)


class ModuleOverview(BaseModel):
    Module: ModuleClass
    StatusHistory: List[ModuleStatus]
    Objects: List[ModuleObjectShort]


def view_module_overview_endpoint(
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
) -> ModuleOverview:
    subq = (
        select(
            ModuleObjectsTable,
            func.row_number()
            .over(
                partition_by=ModuleObjectsTable.Code,
                order_by=desc(ModuleObjectsTable.Modified_Date),
            )
            .label("_RowNumber"),
        )
        .filter(ModuleObjectsTable.Module_ID == module.Module_ID)
        .subquery()
    )

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

    rows: Sequence[ModuleObjectsTable] = session.execute(stmt).scalars().all()
    objects: List[ModuleObjectShort] = [ModuleObjectShort.model_validate(r) for r in rows]
    status_history: List[ModuleStatus] = [ModuleStatus.model_validate(s) for s in module.status_history]

    response = ModuleOverview(
        Module=ModuleClass.model_validate(module),
        StatusHistory=status_history,
        Objects=objects,
    )
    return response
