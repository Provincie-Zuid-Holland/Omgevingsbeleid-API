from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.orm import undefer

from app.dynamic.db.tables import ObjectsTable
from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortedPagination
from app.extensions.areas.db.tables import AreasTable
from app.extensions.areas.models.models import GeometryFunctions

SPATIAL_FUNCTION_MAP = {
    GeometryFunctions.CONTAINS: "STContains",
    GeometryFunctions.WITHIN: "STWithin",
    GeometryFunctions.OVERLAPS: "STOverlaps",
    GeometryFunctions.INTERSECTS: "STIntersects",
}


class AreaRepository(BaseRepository):
    def get_by_uuid(self, uuidx: UUID) -> Optional[AreasTable]:
        stmt = select(AreasTable).filter(AreasTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_by_werkingsgebied_uuid(self, werkingsgebied_uuid: UUID) -> Optional[AreasTable]:
        stmt = select(AreasTable).filter(AreasTable.Source_UUID == werkingsgebied_uuid)
        return self.fetch_first(stmt)

    def get_with_gml(self, uuidx: UUID) -> Optional[AreasTable]:
        stmt = select(AreasTable).options(undefer(AreasTable.Gml)).filter(AreasTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_many_with_gml(self, uuids: List[UUID]) -> List[AreasTable]:
        if len(uuids) == 0:
            return []

        stmt = select(AreasTable).options(undefer("Gml")).filter(AreasTable.UUID.in_(uuids))
        return self.fetch_all(stmt)

    def get_latest_by_areas(
        self,
        area_object_type: str,
        areas: List[UUID],
        object_types: List[str],
        pagination: SortedPagination,
    ) -> PaginatedQueryResult:
        werkingsgebieden_subq = (
            select(
                ObjectsTable,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.Code,
                    order_by=desc(ObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ObjectsTable)
            .filter(ObjectsTable.Object_Type == area_object_type)
        )

        # old
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
        stmt = select(aliased_objects).filter(subq.c.get("_RowNumber") == 1)

        paginated_result = query_paginated(
            query=stmt,
            session=self._db,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(subq.c, pagination.sort.column), pagination.sort.order),
        )

        return paginated_result
