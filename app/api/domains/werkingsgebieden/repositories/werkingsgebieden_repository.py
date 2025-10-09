from sqlalchemy import desc, select
from sqlalchemy.orm import Session, aliased, undefer
from sqlalchemy.sql import func

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.werkingsgebieden import SourceWerkingsgebiedenTable


class WerkingsgebiedenRepository(BaseRepository):
    def get_by_title_paginated(
        self, session: Session, pagination: SortedPagination, title: str
    ) -> PaginatedQueryResult:
        stmt = select(SourceWerkingsgebiedenTable).filter(SourceWerkingsgebiedenTable.Title == title)
        return self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(SourceWerkingsgebiedenTable, pagination.sort.column), pagination.sort.order),
        )

    def get_latest_by_title(self, session: Session, title: str) -> SourceWerkingsgebiedenTable:
        stmt = (
            select(SourceWerkingsgebiedenTable)
            .filter(SourceWerkingsgebiedenTable.Title == title)
            .options(undefer(SourceWerkingsgebiedenTable.SHAPE))
            .order_by(desc(SourceWerkingsgebiedenTable.Created_Date))
        )
        return self.fetch_first(
            session=session,
            statement=stmt,
        )

    def get_unique_paginated(self, session: Session, pagination: SortedPagination) -> PaginatedQueryResult:
        row_number = (
            func.row_number()
            .over(
                partition_by=SourceWerkingsgebiedenTable.Title,
                order_by=desc(SourceWerkingsgebiedenTable.Modified_Date),
            )
            .label("_RowNumber")
        )

        subq = select(
            SourceWerkingsgebiedenTable.UUID,
            SourceWerkingsgebiedenTable.ID,
            SourceWerkingsgebiedenTable.Created_Date,
            SourceWerkingsgebiedenTable.Modified_Date,
            SourceWerkingsgebiedenTable.Start_Validity,
            SourceWerkingsgebiedenTable.End_Validity,
            SourceWerkingsgebiedenTable.Title,
            SourceWerkingsgebiedenTable.Geometry_Hash,
            row_number,
        ).subquery("subq")

        aliased_objects = aliased(SourceWerkingsgebiedenTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1)
        sort_column = getattr(subq.c, pagination.sort.column)

        return self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(sort_column, pagination.sort.order),
        )
