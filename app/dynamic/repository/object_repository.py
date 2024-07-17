from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.sql import and_, func, or_

from app.dynamic.db import ObjectsTable, ObjectStaticsTable
from app.dynamic.models.models import ObjectCount
from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortedPagination


class ObjectRepository(BaseRepository):
    def get_valid_counts(self, user_uuid: UUID) -> List[ObjectCount]:
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
            .filter(
                or_(
                    ObjectStaticsTable.Owner_1_UUID == user_uuid,
                    ObjectStaticsTable.Owner_2_UUID == user_uuid,
                    ObjectStaticsTable.Portfolio_Holder_1_UUID == user_uuid,
                    ObjectStaticsTable.Portfolio_Holder_2_UUID == user_uuid,
                    ObjectStaticsTable.Client_1_UUID == user_uuid,
                ).self_group()
            )
            .filter(ObjectsTable.Start_Validity <= datetime.utcnow())
        )

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.utcnow(),
                    subq.c.End_Validity == None,
                )
            )
        )

        main_query = stmt.subquery()

        final_query = select(main_query.c.Object_Type, func.count()).group_by(main_query.c.Object_Type)

        rows = self._db.execute(final_query).fetchall()
        result = [ObjectCount(Object_Type=r[0], Count=r[1]) for r in rows]
        return result

    def get_by_uuid(self, uuid: UUID) -> Optional[ObjectsTable]:
        stmt = select(ObjectsTable).filter(ObjectsTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_by_object_type_and_uuid(self, object_type: str, uuid: UUID) -> Optional[ObjectsTable]:
        stmt = select(ObjectsTable).filter(ObjectsTable.UUID == uuid).filter(ObjectsTable.Object_Type == object_type)
        return self.fetch_first(stmt)

    def get_latest_valid_by_id(self, object_type: str, object_id: int) -> Optional[ObjectsTable]:
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
            .filter(ObjectsTable.Object_Type == object_type)
            .filter(ObjectsTable.Object_ID == object_id)
            .filter(ObjectsTable.Start_Validity <= datetime.utcnow())
        )

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.utcnow(),
                    subq.c.End_Validity == None,
                )
            )
            .order_by(desc(subq.c.Modified_Date))
        )

        result = self.fetch_first(stmt)
        return result

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
        pagination: SortedPagination,
        owner_uuid: Optional[UUID] = None,
        object_type: Optional[str] = None,
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
            .filter(ObjectsTable.Start_Validity <= datetime.utcnow())
        )

        filters = []
        if owner_uuid is not None:
            owner_filter = or_(
                ObjectStaticsTable.Owner_1_UUID == owner_uuid,
                ObjectStaticsTable.Owner_2_UUID == owner_uuid,
                ObjectStaticsTable.Portfolio_Holder_1_UUID == owner_uuid,
                ObjectStaticsTable.Portfolio_Holder_2_UUID == owner_uuid,
                ObjectStaticsTable.Client_1_UUID == owner_uuid,
            )
            filters.append(owner_filter)

        if object_type is not None:
            filters.append(or_(ObjectsTable.Object_Type == object_type))

        if len(filters) > 0:
            subq = subq.filter(and_(*filters))

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.utcnow(),
                    subq.c.End_Validity == None,
                )
            )
        )

        return self.fetch_paginated(
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(subq.c, pagination.sort.column), pagination.sort.order),
        )
