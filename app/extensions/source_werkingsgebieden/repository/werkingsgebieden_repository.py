from datetime import datetime
from typing import List
from uuid import UUID

from shapely import wkt
from sqlalchemy import desc, select, text
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func

from app.dynamic.db import ObjectsTable
from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortedPagination, query_paginated
from app.extensions.source_werkingsgebieden.db.tables import SourceWerkingsgebiedenTable
from app.extensions.source_werkingsgebieden.models.models import VALID_GEOMETRIES, GeometryFunctions

SPATIAL_FUNCTION_MAP = {
    GeometryFunctions.CONTAINS: "STContains",
    GeometryFunctions.WITHIN: "STWithin",
    GeometryFunctions.OVERLAPS: "STOverlaps",
    GeometryFunctions.INTERSECTS: "STIntersects",
}


class WerkingsgebiedenRepository(BaseRepository):
    def get_all_paginated(self, pagination: SortedPagination) -> PaginatedQueryResult:
        stmt = select(SourceWerkingsgebiedenTable).filter(SourceWerkingsgebiedenTable.End_Validity > datetime.utcnow())
        return self.fetch_paginated(
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(SourceWerkingsgebiedenTable, pagination.sort.column), pagination.sort.order),
        )

    def get_latest_in_area(
        self,
        in_area: List[UUID],
        object_types: List[str],
        pagination: SortedPagination,
    ) -> PaginatedQueryResult:
        """
        Find all latest objects matching a list of Werkingsgebied UUIDs
        """
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

    def get_latest_by_geometry(
        self,
        geometry: str,
        function: GeometryFunctions,
        object_types: List[str],
        pagination: SortedPagination,
    ) -> PaginatedQueryResult:
        # Validating the geometry should have been done already
        # But I do it again here because we insert it as plain text into sql.
        # Better be safe
        try:
            geom = wkt.loads(geometry)
            if geom.geom_type not in VALID_GEOMETRIES:
                raise RuntimeError("Geometry is not a valid shape")
        except Exception as e:
            raise RuntimeError("Geometry is not a valid shape")

        spatial_function = SPATIAL_FUNCTION_MAP[function]
        geometry_filter = f"SHAPE.{spatial_function}(geometry::STGeomFromText('{geometry}', 28992)) = 1"
        timepoint = datetime.utcnow()

        werkingsgebieden = (
            select(SourceWerkingsgebiedenTable.UUID)
            .select_from(SourceWerkingsgebiedenTable)
            .filter(SourceWerkingsgebiedenTable.Start_Validity < timepoint)
            .filter(SourceWerkingsgebiedenTable.End_Validity > timepoint)
            .filter(text(geometry_filter))
            .params(polygon=geometry)
        )

        subq = select(
            ObjectsTable,
            func.row_number()
            .over(
                partition_by=ObjectsTable.Code,
                order_by=desc(ObjectsTable.Modified_Date),
            )
            .label("_RowNumber"),
        ).select_from(ObjectsTable)

        subq = subq.filter(ObjectsTable.Gebied_UUID.in_(werkingsgebieden))
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
