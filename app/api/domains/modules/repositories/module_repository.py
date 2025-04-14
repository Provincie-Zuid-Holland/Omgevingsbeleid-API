from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import aliased

from app.api.base_repository import BaseRepository
from app.api.domains.modules.types import FilterObjectCode, PublicModuleStatusCode
from app.api.utils.pagination import PaginatedQueryResult, SimplePagination, SortOrder
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable
from app.core.tables.objects import ObjectStaticsTable


class ModuleSortColumn(str, Enum):
    Created_Date = "Created_Date"
    Modified_Date = "Modified_Date"


class ModuleSort(BaseModel):
    column: ModuleSortColumn
    order: SortOrder


class ModuleSortedPagination(SimplePagination):
    sort: ModuleSort


class ModuleRepository(BaseRepository):
    def get_by_id(self, id: int) -> Optional[ModuleTable]:
        stmt = select(ModuleTable).where(ModuleTable.Module_ID == id)
        return self.fetch_first(stmt)

    def get_filtered_query(
        self,
        filter_activated: Optional[bool],
        filter_closed: Optional[bool],
        filter_successful: Optional[bool],
        filter_title: Optional[str],
        mine: Optional[UUID],
        object_code: Optional[FilterObjectCode],
    ):
        filters = []
        if filter_activated is not None:
            filters.append(and_(ModuleTable.Activated == filter_activated))
        if filter_closed is not None:
            filters.append(and_(ModuleTable.Closed == filter_closed))
        if filter_successful is not None:
            filters.append(and_(ModuleTable.Successful == filter_successful))
        if filter_title is not None:
            filters.append(and_(ModuleTable.Title.like(filter_title)))

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
        pagination: ModuleSortedPagination,
        filter_activated: Optional[bool] = None,
        filter_closed: Optional[bool] = None,
        filter_successful: Optional[bool] = None,
        filter_title: Optional[str] = None,
        mine: Optional[UUID] = None,
        object_code: Optional[FilterObjectCode] = None,
    ) -> PaginatedQueryResult:
        stmt = self.get_filtered_query(
            filter_activated,
            filter_closed,
            filter_successful,
            filter_title,
            mine,
            object_code,
        )
        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(ModuleTable, pagination.sort.column), pagination.sort.order),
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
