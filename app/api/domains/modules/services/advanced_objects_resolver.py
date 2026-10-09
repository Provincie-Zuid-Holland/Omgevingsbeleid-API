from datetime import UTC, datetime

from sqlalchemy import case, desc, select
from sqlalchemy.orm import Session, aliased, selectinload
from sqlalchemy.sql import func, literal, or_, union_all

from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable
from app.core.tables.objects import ObjectsTable


class AdvancedObjectsResolver:
    def __init__(
        self,
        session: Session,
        columns: set[str],
        valid_timepoint: datetime | None,
        module_timepoint: datetime | None = None,
        filter_object_types: set[str] | None = None,
        filter_codes: set[str] | None = None,
        filter_module_id: int | None = None,
    ):
        self._session: Session = session
        self._columns: set[str] = columns.union(
            {
                # Used by the queries
                "object_type",
                "code",
                "modified_date",
                "start_validity",
                "end_validity",
            }
        )

        timepoint: datetime = datetime.now(UTC)
        self._valid_timepoint: datetime = valid_timepoint or timepoint
        self._module_timepoint: datetime = module_timepoint or self._valid_timepoint

        self._filter_object_types: set[str] | None = filter_object_types
        self._filter_codes: set[str] | None = filter_codes
        self._filter_module_id: int | None = filter_module_id

    def fetch_objects(self):
        object_query = self._get_object_query()

        # We only query the modules table if we have a Module ID
        if self._filter_module_id:
            module_query = self._get_module_object_query()
            union_query = (
                union_all(
                    # alias().select() is a cheat to force parentheses
                    # Else the union might fail on sqlite
                    (object_query.alias().select()),
                    (module_query.alias().select()),
                )
            ).alias("combined")
        else:
            # if we don't have a module id then we just promote the objects query as the unioned query
            union_query = object_query.alias("combined")

        row_number_query = select(
            union_query.c.module_id,
            union_query.c._terminated,
            *[getattr(union_query.c, f) for f in self._columns],
            func.row_number()
            .over(partition_by=union_query.c.code, order_by=desc(union_query.c.module_id))
            .label("_rnk"),
        ).alias("ranked_results")

        final_query = (
            select(
                row_number_query.c.module_id,
                *[getattr(row_number_query.c, f) for f in self._columns],
            )
            .filter(row_number_query.c._rnk == 1)
            .filter(row_number_query.c._terminated == 0)
        )

        result = self._session.execute(final_query)
        return result

    def _get_object_query(self):
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
            .filter(ObjectsTable.start_validity < self._valid_timepoint)
        )

        # Inner filters
        if self._filter_object_types:
            subq = subq.filter(ObjectsTable.object_type.in_(self._filter_object_types))
        if self._filter_codes:
            subq = subq.filter(ObjectsTable.code.in_(self._filter_codes))

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(
                literal(0).label("module_id"),
                literal(0).label("_terminated"),
                *[getattr(aliased_objects, f) for f in self._columns],
            )
            .filter(subq.c._row_number == 1)
            .filter(
                or_(
                    subq.c.end_validity >= self._valid_timepoint,
                    subq.c.end_validity.is_(None),
                )
            )
            .order_by(desc(subq.c.modified_date))
        )
        return stmt

    def _get_module_object_query(self):
        query = (
            select(
                ModuleObjectsTable,
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.code,
                    order_by=desc(ModuleObjectsTable.modified_date),
                )
                .label("_row_number"),
                case((ModuleObjectContextTable.action == "Terminate", 1), else_=0).label("_terminated"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleObjectsTable.module_object_context)
            .filter(ModuleObjectsTable.modified_date < self._module_timepoint)
            .filter(ModuleObjectContextTable.hidden == False)
        )

        # Inner filters
        if self._filter_module_id:
            query = query.filter(ModuleObjectsTable.module_id == self._filter_module_id)
        if self._filter_object_types:
            query = query.filter(ModuleObjectsTable.object_type.in_(self._filter_object_types))
        if self._filter_codes:
            query = query.filter(ModuleObjectsTable.code.in_(self._filter_codes))

        subq = query.subquery()

        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = (
            select(
                aliased_objects.module_id,
                subq.c._terminated,
                *[getattr(aliased_objects, f) for f in self._columns],
            )
            .filter(subq.c._row_number == 1)
            .filter(subq.c.deleted == False)
        )
        return stmt


class AdvancedObjectsResolverFactory:
    def create_service(
        self,
        session: Session,
        columns: set[str],
        valid_timepoint: datetime | None,
        module_timepoint: datetime | None = None,
        filter_object_types: set[str] | None = None,
        filter_codes: set[str] | None = None,
        filter_module_id: int | None = None,
    ) -> AdvancedObjectsResolver:
        return AdvancedObjectsResolver(
            session,
            columns,
            valid_timepoint,
            module_timepoint,
            filter_object_types,
            filter_codes,
            filter_module_id,
        )
