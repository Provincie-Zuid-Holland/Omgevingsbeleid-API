from typing import Optional, List
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session
from app.dynamic.db import ObjectStaticsTable
from app.dynamic.dependencies import FilterObjectCode

from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleTable


class ModuleRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_by_id(self, id: int) -> Optional[ModuleTable]:
        stmt = select(ModuleTable).where(ModuleTable.Module_ID == id)
        maybe_module = self._db.scalars(stmt).first()

        return maybe_module

    def get_with_filters(
        self,
        only_active: bool,
        mine: Optional[UUID],
        maybe_filter_code: Optional[FilterObjectCode],
    ) -> List[ModuleTable]:
        filters = []
        if only_active:
            filters.append(and_(ModuleTable.Closed == False))

        if mine is not None:
            filters.append(
                and_(
                    or_(
                        ModuleTable.Module_Manager_1_UUID == mine,
                        ModuleTable.Module_Manager_2_UUID == mine,
                        ObjectStaticsTable.Owner_1_UUID == mine,
                        ObjectStaticsTable.Owner_2_UUID == mine,
                    )
                )
            )

        if maybe_filter_code is not None:
            filters.append(
                and_(ModuleObjectContextTable.Code == maybe_filter_code.get_code())
            )

        stmt = (
            select(ModuleTable)
            .distinct()
            .select_from(ModuleTable)
            .outerjoin(ModuleObjectsTable)
            .outerjoin(
                ModuleObjectContextTable,
                ModuleObjectsTable.Module_ID == ModuleObjectContextTable.Module_ID
                and ModuleObjectsTable.Code == ModuleObjectContextTable.Code,
            )
            .outerjoin(ObjectStaticsTable)
            .filter(*filters)
        )

        rows: List[ModuleTable] = [r for r, in self._db.execute(stmt).all()]
        return rows
