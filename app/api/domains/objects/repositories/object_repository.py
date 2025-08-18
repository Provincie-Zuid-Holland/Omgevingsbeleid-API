from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, aliased, selectinload
from sqlalchemy.sql import and_, func, or_

from app.api.base_repository import BaseRepository
from app.api.domains.objects.types import ObjectCount
from app.api.types import PreparedQuery
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable


class ObjectRepository(BaseRepository):
    def get_valid_counts(self, session: Session, user_uuid: UUID) -> List[ObjectCount]:
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
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
        )

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.now(timezone.utc),
                    subq.c.End_Validity.is_(None),
                )
            )
        )
        main_query = stmt.subquery()

        final_query = select(main_query.c.Object_Type, func.count()).group_by(main_query.c.Object_Type)

        rows = session.execute(final_query).fetchall()
        result = [ObjectCount(object_type=r[0], count=r[1]) for r in rows]
        return result

    def get_by_uuid(self, session: Session, uuid: UUID) -> Optional[ObjectsTable]:
        stmt = select(ObjectsTable).filter(ObjectsTable.UUID == uuid)
        return self.fetch_first(session, stmt)

    def get_by_object_type_and_uuid(self, session: Session, object_type: str, uuid: UUID) -> Optional[ObjectsTable]:
        stmt = select(ObjectsTable).filter(ObjectsTable.UUID == uuid).filter(ObjectsTable.Object_Type == object_type)
        return self.fetch_first(session, stmt)

    def get_next_valid_object(self, session: Session, object_uuid: UUID) -> Optional[ObjectsTable]:
        reference_obj = (select(ObjectsTable).filter(ObjectsTable.UUID == object_uuid)).subquery()

        stmt = (
            select(ObjectsTable)
            .options(selectinload(ObjectsTable.ObjectStatics))
            .join(ObjectsTable.ObjectStatics)
            .filter(ObjectsTable.Code == reference_obj.c.Code)
            .filter(ObjectsTable.Modified_Date > reference_obj.c.Modified_Date)
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
            .order_by(ObjectsTable.Modified_Date.asc())
        )
        stmt = stmt.filter(
            or_(
                ObjectsTable.End_Validity > datetime.now(timezone.utc),
                ObjectsTable.End_Validity.is_(None),
            )
        )

        return self.fetch_first(session, stmt)

    def get_latest_valid_by_id(self, session: Session, object_type: str, object_id: int) -> Optional[ObjectsTable]:
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
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
        )

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.now(timezone.utc),
                    subq.c.End_Validity.is_(None),
                )
            )
            .order_by(desc(subq.c.Modified_Date))
        )
        result = self.fetch_first(session, stmt)
        return result

    def get_latest_by_id(self, session: Session, object_type: str, object_id: int) -> Optional[ObjectsTable]:
        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.Object_Type == object_type)
            .filter(ObjectsTable.Object_ID == object_id)
            .order_by(desc(ObjectsTable.Modified_Date))
        )
        return self.fetch_first(session, stmt)

    def get_latest_filtered(
        self,
        session: Session,
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
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
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
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1)

        return self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(subq.c, pagination.sort.column), pagination.sort.order),
        )

    def prepare_list_valid_lineages(self, object_type: str, filter_title: Optional[str] = None) -> PreparedQuery:
        subq = (
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
            .filter(ObjectsTable.Object_Type == object_type)
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
            .subquery()
        )

        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.now(timezone.utc),
                    subq.c.End_Validity.is_(None),
                )
            )
        )
        if filter_title:
            stmt = stmt.filter(subq.c.Title.like(filter_title))

        return PreparedQuery(
            query=stmt,
            aliased_ref=aliased_objects,
        )

    def prepare_list_valid_lineage_tree(self, object_type: str, lineage_id: int) -> PreparedQuery:
        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.Object_Type == object_type)
            .filter(ObjectsTable.Object_ID == lineage_id)
        )
        return PreparedQuery(
            query=stmt,
            aliased_ref=ObjectsTable,
        )
