from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.api.base_repository import BaseRepository
from app.api.domains.modules.types import PublicModuleStatusCode
from app.api.domains.objects.types import FilterObjectCode
from app.api.utils.pagination import PaginatedQueryResult, SimplePagination, SortedPagination
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable
from app.core.tables.objects import ObjectStaticsTable


class ModuleRepository(BaseRepository):
    def get_by_id(self, session: Session, id: int) -> ModuleTable | None:
        stmt = select(ModuleTable).where(ModuleTable.module_id == id)
        return self.fetch_first(session, stmt)

    def get_filtered_query(
        self,
        filter_activated: bool | None,
        filter_closed: bool | None,
        filter_successful: bool | None,
        filter_title: str | None,
        mine: UUID | None,
        object_code: FilterObjectCode | None,
    ):
        filters = []
        if filter_activated is not None:
            filters.append(and_(ModuleTable.activated == filter_activated))
        if filter_closed is not None:
            filters.append(and_(ModuleTable.closed == filter_closed))
        if filter_successful is not None:
            filters.append(and_(ModuleTable.successful == filter_successful))
        if filter_title is not None:
            filters.append(and_(ModuleTable.title.like(filter_title)))

        if mine is not None:
            filters.append(
                and_(
                    or_(
                        ModuleTable.module_manager_1_id == mine,
                        ModuleTable.module_manager_2_id == mine,
                        ObjectStaticsTable.owner_1_id == mine,
                        ObjectStaticsTable.owner_2_id == mine,
                        ObjectStaticsTable.portfolio_holder_1_id == mine,
                        ObjectStaticsTable.portfolio_holder_2_id == mine,
                        ObjectStaticsTable.client_1_id == mine,
                    ).self_group()
                ).self_group()
            )

        if object_code is not None:
            filters.append(and_(ModuleObjectContextTable.code == object_code.get_code()))

        stmt = (
            select(ModuleTable)
            .distinct()
            .select_from(ModuleTable)
            .outerjoin(ModuleObjectsTable)
            .outerjoin(
                ModuleObjectContextTable,
                ModuleObjectsTable.module_id == ModuleObjectContextTable.module_id
                and ModuleObjectsTable.code == ModuleObjectContextTable.code,
            )
            .outerjoin(ObjectStaticsTable, ObjectStaticsTable.code == ModuleObjectsTable.code)
            .filter(*filters)
        )

        return stmt

    def get_with_filters(
        self,
        session: Session,
        pagination: SortedPagination,
        filter_activated: bool | None = None,
        filter_closed: bool | None = None,
        filter_successful: bool | None = None,
        filter_title: str | None = None,
        mine: UUID | None = None,
        object_code: FilterObjectCode | None = None,
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
            session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(ModuleTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result

    def get_public_modules(self, session: Session, pagination: SimplePagination):
        subq = select(
            ModuleStatusHistoryTable,
            func.row_number()
            .over(
                partition_by=ModuleStatusHistoryTable.module_id,
                order_by=desc(ModuleStatusHistoryTable.created_date),
            )
            .label("_row_number"),
        )

        subq = subq.subquery()
        aliased_objects = aliased(ModuleStatusHistoryTable, subq)
        stmt = (
            select(aliased_objects, ModuleTable)
            .join(ModuleTable)
            .filter(subq.c._row_number == 1)
            .filter(ModuleTable.closed == False)
            .filter(subq.c.status.in_(PublicModuleStatusCode.values()))
            .order_by(desc(ModuleTable.module_id))
        )

        paged_result = self.fetch_paginated_no_scalars(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
        )
        return paged_result
