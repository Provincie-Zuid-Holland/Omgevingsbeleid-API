from typing import Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.sql import and_, func, or_

from app.dynamic.db.object_static_table import ObjectStaticsTable
from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult


class ObjectRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[ObjectsTable]:
        stmt = select(ObjectsTable).filter(ObjectsTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_by_object_type_and_uuid(self, object_type: str, uuid: UUID) -> Optional[ObjectsTable]:
        stmt = select(ObjectsTable).filter(ObjectsTable.UUID == uuid).filter(ObjectsTable.Object_Type == object_type)
        return self.fetch_first(stmt)

    def get_latest_by_id(self, object_type: str, object_id: int) -> Optional[ObjectsTable]:
        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.Object_Type == object_type)
            .filter(ObjectsTable.Object_ID == object_id)
            .order_by(desc(ObjectsTable.Modified_Date))
        )
        return self.fetch_first(stmt)

    def get_latest_filtered(
        self,
        owner_uuid: Optional[UUID] = None,
        object_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
        sort: str = "desc",
    ) -> PaginatedQueryResult:
        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.Code,
                order_by=desc(ObjectsTable.Modified_Date),
            )
            .label("_RowNumber")
        )

        subq = (
            select(ObjectsTable, row_number)
            .options(selectinload(ObjectsTable.ObjectStatics))
            .join(ObjectsTable.ObjectStatics)
        )

        filters = []
        if owner_uuid is not None:
            owner_filter = or_(
                ObjectStaticsTable.Owner_1_UUID == owner_uuid,
                ObjectStaticsTable.Owner_2_UUID == owner_uuid,
            )
            filters.append(owner_filter)

        if object_type is not None:
            filters.append(or_(ObjectsTable.Object_Type == object_type))

        if len(filters) > 0:
            subq = subq.filter(and_(*filters))

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1)

        return self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(subq.c.Object_ID, sort),
        )
        # return self.fetch_all(stmt)
