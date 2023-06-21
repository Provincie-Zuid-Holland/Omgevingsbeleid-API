from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import func
from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.utils.pagination import PagedResponse, query_paginated

from app.extensions.werkingsgebieden.db.tables import WerkingsgebiedenTable
from app.extensions.werkingsgebieden.models.models import (
    GeoSearchResult,
)


class WerkingsgebiedenRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_all(self) -> List[WerkingsgebiedenTable]:
        stmt = select(WerkingsgebiedenTable).order_by(
            desc(WerkingsgebiedenTable.Modified_Date)
        )

        rows: List[WerkingsgebiedenTable] = self._db.scalars(stmt).all()
        return rows

    # TODO: Object type filter
    @staticmethod
    def latest_objects_query(in_area: Optional[List[UUID]]):
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

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c.get("_RowNumber") == 1)
            .order_by(desc(subq.c.Modified_Date))
        )
        return stmt

    def get_latest_in_area(
        self, in_area: List[UUID], offset=0, limit=-1
    ) -> PagedResponse[GeoSearchResult]:
        """
        Find all latest objects matching a list of Werkingsgebied UUIDs
        """
        query = self.latest_objects_query(in_area=in_area)

        table_rows, total_count = query_paginated(
            query=query, session=self._db, limit=limit, offset=offset
        )

        object_list = []
        for item in table_rows:
            search_result = GeoSearchResult(
                Gebied=str(item.Gebied_UUID),
                Titel=item.Title,
                Omschrijving=item.Description,
                Type=item.Object_Type,
                UUID=item.UUID,
            )
            object_list.append(search_result)

        return PagedResponse(
            total=total_count, limit=limit, offset=offset, results=object_list
        )
