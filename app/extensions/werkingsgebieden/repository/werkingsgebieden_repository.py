from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func

from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortedPagination, query_paginated
from app.extensions.werkingsgebieden.db.tables import WerkingsgebiedenTable


class WerkingsgebiedenRepository(BaseRepository):
    def get_all(self) -> List[WerkingsgebiedenTable]:
        stmt = select(WerkingsgebiedenTable).order_by(desc(WerkingsgebiedenTable.Modified_Date))
        return self.fetch_all(stmt)

    def get_all_paginated(self, pagination: SortedPagination) -> PaginatedQueryResult:
        stmt = select(WerkingsgebiedenTable).order_by(desc(WerkingsgebiedenTable.Modified_Date))
        return self.fetch_paginated(
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(WerkingsgebiedenTable, pagination.sort.column), pagination.sort.order),
        )

    @staticmethod
    def latest_objects_query(in_area: Optional[List[UUID]], object_types: List[str]):
        subq = select(
            ObjectsTable,
            func.row_number()
            .over(
                partition_by=ObjectsTable.Code,
                order_by=desc(ObjectsTable.Modified_Date),
            )
            .label("_RowNumber"),
        ).select_from(ObjectsTable)

        if in_area:
            subq = subq.filter(ObjectsTable.Gebied_UUID.in_(in_area))

        if object_types:
            subq = subq.filter(ObjectsTable.Object_Type.in_(object_types))

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c.get("_RowNumber") == 1).order_by(desc(subq.c.Modified_Date))
        return stmt

    def get_latest_in_area(
        self,
        in_area: List[UUID],
        object_types: List[str],
        pagination: SortedPagination,
    ) -> PaginatedQueryResult:
        """
        Find all latest objects matching a list of Werkingsgebied UUIDs
        """
        query = self.latest_objects_query(in_area=in_area, object_types=object_types)

        paginated_result = query_paginated(
            query=query,
            session=self._db,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(ObjectsTable, pagination.sort.column), pagination.sort.order),
        )

        return paginated_result
