from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, aliased, joinedload, selectinload
from sqlalchemy.sql import and_, func, or_

from app.api.base_repository import BaseRepository
from app.api.domains.objects.types import ObjectCount
from app.api.types import PreparedQuery
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable


class ObjectRepository(BaseRepository):
    def get_valid_counts(self, session: Session, user_uuid: UUID) -> list[ObjectCount]:
        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.code,
                order_by=desc(ObjectsTable.modified_date),
            )
            .label("_row_number")
        )

        subq = (
            select(ObjectsTable, row_number)
            .options(selectinload(ObjectsTable.object_statics))
            .join(ObjectsTable.object_statics)
            .filter(
                or_(
                    ObjectStaticsTable.owner_1_id == user_uuid,
                    ObjectStaticsTable.owner_2_id == user_uuid,
                    ObjectStaticsTable.portfolio_holder_1_id == user_uuid,
                    ObjectStaticsTable.portfolio_holder_2_id == user_uuid,
                    ObjectStaticsTable.client_1_id == user_uuid,
                ).self_group()
            )
            .filter(ObjectsTable.start_validity <= datetime.now(UTC))
        )

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._row_number == 1)
            .filter(
                or_(
                    subq.c.end_validity > datetime.now(UTC),
                    subq.c.end_validity.is_(None),
                )
            )
        )
        main_query = stmt.subquery()

        final_query = select(main_query.c.object_type, func.count()).group_by(main_query.c.object_type)

        rows = session.execute(final_query).fetchall()
        result = [ObjectCount(object_type=r[0], count=r[1]) for r in rows]
        return result

    def get_by_id(self, session: Session, idx: UUID) -> ObjectsTable | None:
        stmt = select(ObjectsTable).filter(ObjectsTable.id == idx)
        return self.fetch_first(session, stmt)

    def get_by_object_type_and_id(self, session: Session, object_type: str, idx: UUID) -> ObjectsTable | None:
        stmt = select(ObjectsTable).filter(ObjectsTable.id == idx).filter(ObjectsTable.object_type == object_type)
        return self.fetch_first(session, stmt)

    def get_next_valid_object(self, session: Session, object_uuid: UUID) -> ObjectsTable | None:
        reference_obj = (select(ObjectsTable).filter(ObjectsTable.id == object_uuid)).subquery()

        stmt = (
            select(ObjectsTable)
            .options(selectinload(ObjectsTable.object_statics))
            .join(ObjectsTable.object_statics)
            .filter(ObjectsTable.code == reference_obj.c.code)
            .filter(ObjectsTable.modified_date > reference_obj.c.modified_date)
            .filter(ObjectsTable.start_validity <= datetime.now(UTC))
            .order_by(ObjectsTable.modified_date.asc())
        )
        stmt = stmt.filter(
            or_(
                ObjectsTable.end_validity > datetime.now(UTC),
                ObjectsTable.end_validity.is_(None),
            )
        )

        return self.fetch_first(session, stmt)

    def get_latest_valid_by_id(self, session: Session, object_type: str, object_id: int) -> ObjectsTable | None:
        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.code,
                order_by=desc(ObjectsTable.modified_date),
            )
            .label("_row_number")
        )

        subq = (
            select(ObjectsTable, row_number)
            .options(selectinload(ObjectsTable.object_statics))
            .join(ObjectsTable.object_statics)
            .filter(ObjectsTable.object_type == object_type)
            .filter(ObjectsTable.object_id == object_id)
            .filter(ObjectsTable.start_validity <= datetime.now(UTC))
        )

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._row_number == 1)
            .filter(
                or_(
                    subq.c.end_validity > datetime.now(UTC),
                    subq.c.end_validity.is_(None),
                )
            )
            .order_by(desc(subq.c.modified_date))
        )
        result = self.fetch_first(session, stmt)
        return result

    def get_latest_by_id(self, session: Session, object_type: str, object_id: int) -> ObjectsTable | None:
        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.object_type == object_type)
            .filter(ObjectsTable.object_id == object_id)
            .order_by(desc(ObjectsTable.modified_date))
        )
        return self.fetch_first(session, stmt)

    def get_latest_filtered(
        self,
        session: Session,
        pagination: SortedPagination,
        owner_id: UUID | None = None,
        object_types: Sequence[str] = (),
    ) -> PaginatedQueryResult:
        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.code,
                order_by=desc(ObjectsTable.modified_date),
            )
            .label("_row_number")
        )

        subq = (
            select(ObjectsTable, row_number)
            .options(joinedload(ObjectsTable.object_statics))
            .join(ObjectsTable.object_statics)
            .filter(ObjectsTable.start_validity <= datetime.now(UTC))
        )

        filters = []
        if owner_id is not None:
            owner_filter = or_(
                ObjectStaticsTable.owner_1_id == owner_id,
                ObjectStaticsTable.owner_2_id == owner_id,
                ObjectStaticsTable.portfolio_holder_1_id == owner_id,
                ObjectStaticsTable.portfolio_holder_2_id == owner_id,
                ObjectStaticsTable.client_1_id == owner_id,
            )
            filters.append(owner_filter)

        if object_types:
            filters.append(ObjectsTable.object_type.in_(object_types))

        if len(filters) > 0:
            subq = subq.filter(and_(*filters))

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._row_number == 1)

        return self.fetch_paginated(
            session=session,
            statement=stmt,
            limit=pagination.limit,
            offset=pagination.offset,
            sort=(getattr(subq.c, pagination.sort.column), pagination.sort.order),
        )

    def prepare_list_valid_lineages(self, object_type: str, filter_title: str | None = None) -> PreparedQuery:
        subq = (
            select(
                ObjectsTable,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.code,
                    order_by=desc(ObjectsTable.modified_date),
                )
                .label("_row_number"),
            )
            .select_from(ObjectsTable)
            .filter(ObjectsTable.object_type == object_type)
            .filter(ObjectsTable.start_validity <= datetime.now(UTC))
            .subquery()
        )

        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._row_number == 1)
            .filter(
                or_(
                    subq.c.end_validity > datetime.now(UTC),
                    subq.c.end_validity.is_(None),
                )
            )
        )
        if filter_title:
            stmt = stmt.filter(subq.c.title.like(filter_title))

        return PreparedQuery(
            query=stmt,
            aliased_ref=aliased_objects,
        )

    def prepare_list_valid_lineage_tree(self, object_type: str, lineage_id: int) -> PreparedQuery:
        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.object_type == object_type)
            .filter(ObjectsTable.object_id == lineage_id)
        )
        return PreparedQuery(
            query=stmt,
            aliased_ref=ObjectsTable,
        )
