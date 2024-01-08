from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.sql import and_, func, or_

from app.dynamic.db import ObjectStaticsTable
from app.dynamic.dependencies import FilterObjectCode
from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SimplePagination
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.models.models import PublicModuleStatusCode


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
                        ObjectStaticsTable.Portfolio_Holder_1_UUID == mine,
                        ObjectStaticsTable.Portfolio_Holder_2_UUID == mine,
                        ObjectStaticsTable.Client_1_UUID == mine,
                    ).self_group()
                ).self_group()
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
            .outerjoin(ObjectStaticsTable, ObjectStaticsTable.Code == ModuleObjectsTable.Code)
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

    def get_public_modules(self, pagination: SimplePagination):
        subq = select(
            ModuleStatusHistoryTable,
            func.row_number()
            .over(
                partition_by=ModuleStatusHistoryTable.Module_ID,
                order_by=desc(ModuleStatusHistoryTable.Created_Date),
            )
            .label("_RowNumber"),
        )

        subq = subq.subquery()
        aliased_objects = aliased(ModuleStatusHistoryTable, subq)
        stmt = (
            select(aliased_objects, ModuleTable)
            .join(ModuleTable)
            .filter(subq.c._RowNumber == 1)
            .filter(ModuleTable.Closed == False)
            .filter(subq.c.Status.in_(PublicModuleStatusCode.values()))
            .order_by(desc(ModuleTable.Module_ID))
        )

        paged_result = self.fetch_paginated_no_scalars(
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
        )
        return paged_result
