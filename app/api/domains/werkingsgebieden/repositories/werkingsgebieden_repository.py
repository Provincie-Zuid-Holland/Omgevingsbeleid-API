from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, undefer
from sqlalchemy.sql import func

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.werkingsgebieden import SourceWerkingsgebiedenTable


class WerkingsgebiedenRepository(BaseRepository):
    async def get_by_title_paginated(
        self, session: AsyncSession, pagination: SortedPagination, title: str
    ) -> PaginatedQueryResult:
        stmt = select(SourceWerkingsgebiedenTable).filter(SourceWerkingsgebiedenTable.title == title)
        return await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(SourceWerkingsgebiedenTable, pagination.sort.column), pagination.sort.order),
        )

    async def get_latest_by_title(self, session: AsyncSession, title: str) -> SourceWerkingsgebiedenTable:
        stmt = (
            select(SourceWerkingsgebiedenTable)
            .filter(SourceWerkingsgebiedenTable.title == title)
            .options(undefer(SourceWerkingsgebiedenTable.shape))
            .order_by(desc(SourceWerkingsgebiedenTable.created_date))
        )
        return await self.fetch_first(
            session=session,
            statement=stmt,
        )

    async def get_unique_paginated(self, session: AsyncSession, pagination: SortedPagination) -> PaginatedQueryResult:
        row_number = (
            func.row_number()
            .over(
                partition_by=SourceWerkingsgebiedenTable.title,
                order_by=desc(SourceWerkingsgebiedenTable.modified_date),
            )
            .label("_row_number")
        )

        subq = select(
            SourceWerkingsgebiedenTable.id,
            SourceWerkingsgebiedenTable.ref_id,
            SourceWerkingsgebiedenTable.created_date,
            SourceWerkingsgebiedenTable.modified_date,
            SourceWerkingsgebiedenTable.start_validity,
            SourceWerkingsgebiedenTable.end_validity,
            SourceWerkingsgebiedenTable.title,
            SourceWerkingsgebiedenTable.geometry_hash,
            row_number,
        ).subquery("subq")

        aliased_objects = aliased(SourceWerkingsgebiedenTable, subq)
        stmt = select(aliased_objects).filter(subq.c._row_number == 1)
        sort_column = getattr(subq.c, pagination.sort.column)

        return await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(sort_column, pagination.sort.order),
        )
