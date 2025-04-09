from enum import Enum
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.orm import aliased, undefer

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination, query_paginated
from app.core.tables.objects import ObjectsTable
from app.core.tables.others import AreasTable

VALID_GEOMETRIES = ["Polygon", "Point"]


class GeometryFunctions(str, Enum):
    # Determines if the geometry is entirely contained within the Werkingsgebied.
    CONTAINS = "CONTAINS"
    # It's the inverse of Contains. It determines the Werkingsgebied is entirely within the given geometry
    WITHIN = "WITHIN"
    # Determines in the geometry and Werkingsgebied overlap
    OVERLAPS = "OVERLAPS"
    # If a geometry instance intersects another geometry instance
    INTERSECTS = "INTERSECTS"


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
        # Get newest from werkingsgebieden lineage
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
        ).subquery()

        # Then filter on requirements for werkingsgebieden
        aliased_werkingsgebieden = aliased(ObjectsTable, werkingsgebieden_subq)
        werkingsgebieden_stmt = (
            select(aliased_werkingsgebieden)
            .filter(werkingsgebieden_subq.c.get("_RowNumber") == 1)
            .filter(werkingsgebieden_subq.c.get("Area_UUID").in_(areas))
        ).cte("werkingsgebieden_stmt")

        # Get the newest versions of all `object_types` objects
        objects_subq = (
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
            .filter(ObjectsTable.Object_Type.in_(object_types))
        ).subquery()

        # Finally filter on the used werkingsgebieden
        aliased_objects = aliased(ObjectsTable, objects_subq)
        stmt = (
            select(aliased_objects)
            .join(werkingsgebieden_stmt, aliased_objects.Werkingsgebied_Code == werkingsgebieden_stmt.c.Code)
            .filter(objects_subq.c.get("_RowNumber") == 1)
        )

        paginated_result = query_paginated(
            query=stmt,
            session=self._db,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(objects_subq.c, pagination.sort.column), pagination.sort.order),
        )

        return paginated_result
