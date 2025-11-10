from typing import Optional, Sequence
import uuid
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import func
from datetime import date
from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.werkingsgebieden import InputGeoWerkingsgebiedenTable


class InputGeoWerkingsgebiedenRepository(BaseRepository):
    def get_by_id(self, session: Session, werkingsgbied_uuid: uuid.UUID) -> Optional[InputGeoWerkingsgebiedenTable]:
        stmt = select(InputGeoWerkingsgebiedenTable).where(InputGeoWerkingsgebiedenTable.UUID == werkingsgbied_uuid)
        return self.fetch_first(session, stmt)

    def get_by_title_paginated(
        self, session: Session, title: str, from_date: Optional[date]
    ) -> Sequence[InputGeoWerkingsgebiedenTable]:
        stmt = select(InputGeoWerkingsgebiedenTable).filter(InputGeoWerkingsgebiedenTable.Title == title)
        if from_date:
            stmt = stmt.filter(InputGeoWerkingsgebiedenTable.Created_Date >= from_date)

        result: Sequence[InputGeoWerkingsgebiedenTable] = session.scalars(stmt).all()
        return result

    def get_unique_paginated(self, session: Session, pagination: SortedPagination) -> PaginatedQueryResult:
        row_number = (
            func.row_number()
            .over(
                partition_by=InputGeoWerkingsgebiedenTable.Title,
                order_by=desc(InputGeoWerkingsgebiedenTable.Created_Date),
            )
            .label("_RowNumber")
        )

        subq = select(
            InputGeoWerkingsgebiedenTable,
            row_number,
        ).subquery("subq")

        aliased_objects = aliased(InputGeoWerkingsgebiedenTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1)
        sort_column = getattr(subq.c, pagination.sort.column)

        return self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(sort_column, pagination.sort.order),
        )
