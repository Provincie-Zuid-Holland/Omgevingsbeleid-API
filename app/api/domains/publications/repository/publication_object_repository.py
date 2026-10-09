from collections.abc import Sequence
from datetime import datetime
from typing import Final

from sqlalchemy import case, desc, select
from sqlalchemy.orm import Session, aliased, selectinload
from sqlalchemy.sql import func, literal, or_, union_all

from app.api.base_repository import BaseRepository
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable
from app.core.tables.objects import ObjectsTable

PUBLICATION_BASE_FIELDS: Final[set[str]] = {
    "id",
    "object_type",
    "object_id",
    "code",
    "hierarchy_code",
    "created_date",
    "modified_date",
}


class PublicationObjectRepository(BaseRepository):
    def fetch_objects(
        self,
        session: Session,
        module_id: int,
        timepoint: datetime,
        object_types: Sequence[str] = (),
        requested_fields: Sequence[str] = (),
    ) -> list[dict]:
        fields: set[str] = PUBLICATION_BASE_FIELDS.union(set(requested_fields))

        query = self._get_full_query(module_id, timepoint, object_types, fields)
        result = session.execute(query)
        rows = [row._asdict() for row in result]
        return rows

    def _get_object_query(
        self,
        timepoint: datetime,
        object_types: Sequence[str],
        field_map: set[str],
    ):
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
            .filter(ObjectsTable.start_validity < timepoint)
        )

        if object_types:
            subq = subq.filter(ObjectsTable.object_type.in_(object_types))

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(
                literal(0).label("module_id"),
                literal(0).label("_Terminated"),
                *[getattr(aliased_objects, f) for f in field_map],
            )
            .filter(subq.c._row_number == 1)
            .filter(
                or_(
                    subq.c.end_validity >= timepoint,
                    subq.c.end_validity.is_(None),
                )
            )
            .order_by(desc(subq.c.modified_date))
        )
        return stmt

    def _get_module_object_query(
        self,
        module_id: int,
        timepoint: datetime,
        object_types: Sequence[str],
        field_map: set[str],
    ):
        query = (
            select(
                ModuleObjectsTable,
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.code,
                    order_by=desc(ModuleObjectsTable.modified_date),
                )
                .label("_row_number"),
                case((ModuleObjectContextTable.action == "Terminate", 1), else_=0).label("_Terminated"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleObjectsTable.module_object_context)
            .filter(ModuleObjectsTable.module_id == module_id)
            .filter(ModuleObjectsTable.modified_date < timepoint)
            .filter(ModuleObjectContextTable.hidden == False)
        )

        if object_types:
            query = query.filter(ModuleObjectsTable.object_type.in_(object_types))

        subq = query.subquery()

        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = (
            select(
                aliased_objects.module_id,
                subq.c._Terminated,
                *[getattr(aliased_objects, f) for f in field_map],
            )
            .filter(subq.c._row_number == 1)
            .filter(subq.c.deleted == False)
        )
        return stmt

    def _get_full_query(
        self,
        module_id: int,
        timepoint: datetime,
        object_types: Sequence[str],
        field_map: set[str],
    ):
        object_query = self._get_object_query(timepoint, object_types, field_map)
        module_query = self._get_module_object_query(module_id, timepoint, object_types, field_map)
        union_query = (
            union_all(
                # alias().select() is a cheat to force parentheses
                # Else the union might fail on sqlite
                (object_query.alias().select()),
                (module_query.alias().select()),
            )
        ).alias("combined")

        row_number_query = select(
            union_query.c.module_id,
            union_query.c._Terminated,
            *[getattr(union_query.c, f) for f in field_map],
            func.row_number()
            .over(partition_by=union_query.c.code, order_by=desc(union_query.c.module_id))
            .label("rnk"),
        ).alias("ranked_results")

        final_query = (
            select(
                row_number_query.c.module_id,
                *[getattr(row_number_query.c, f) for f in field_map],
            )
            .filter(row_number_query.c.rnk == 1)
            .filter(row_number_query.c._Terminated == 0)
        )

        return final_query
