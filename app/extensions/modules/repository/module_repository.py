from typing import Optional
from uuid import UUID

from sqlalchemy import and_, or_, select

from app.dynamic.db import ObjectStaticsTable
from app.dynamic.dependencies import FilterObjectCode
from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleTable


class ModuleRepository(BaseRepository):
    def get_by_id(self, id: int) -> Optional[ModuleTable]:
        stmt = select(ModuleTable).where(ModuleTable.Module_ID == id)
        return self.fetch_first(stmt)

    def get_filtered_query(
        self,
        only_active: bool,
        mine: Optional[UUID],
        object_code: Optional[FilterObjectCode],
    ):
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

        if object_code is not None:
            filters.append(and_(ModuleObjectContextTable.Code == object_code.get_code()))

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

        return stmt

    def get_with_filters(
        self,
        only_active: bool,
        mine: Optional[UUID],
        object_code: Optional[FilterObjectCode],
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        stmt = self.get_filtered_query(only_active, mine, object_code)
        paged_result = self.fetch_paginated(
            statement=stmt, offset=offset, limit=limit, sort=(ModuleTable.Modified_Date, "desc")
        )
        return paged_result
