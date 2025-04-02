from sqlalchemy import desc, select
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortedPagination
from app.extensions.source_werkingsgebieden.db.tables import SourceWerkingsgebiedenTable


class WerkingsgebiedenRepository(BaseRepository):
    def get_by_title_paginated(self, pagination: SortedPagination, title: str) -> PaginatedQueryResult:
        stmt = select(SourceWerkingsgebiedenTable).filter(SourceWerkingsgebiedenTable.Title == title)
        return self.fetch_paginated(
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(SourceWerkingsgebiedenTable, pagination.sort.column), pagination.sort.order),
        )

    def get_unique_paginated(self, pagination: SortedPagination) -> PaginatedQueryResult:
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
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(sort_column, pagination.sort.order),
        )
