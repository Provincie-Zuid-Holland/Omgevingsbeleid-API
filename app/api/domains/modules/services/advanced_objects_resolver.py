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
                "Object_Type",
                "Code",
                "Modified_Date",
                "Start_Validity",
                "End_Validity",
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
            # if we dont have a module id then we just promote the objects query as the unioned query
            union_query = object_query.alias("combined")

        row_number_query = select(
            union_query.c.Module_ID,
            union_query.c._Terminated,
            *[getattr(union_query.c, f) for f in self._columns],
            func.row_number()
            .over(partition_by=union_query.c.Code, order_by=desc(union_query.c.Module_ID))
            .label("rnk"),
        ).alias("ranked_results")

        final_query = (
            select(
                row_number_query.c.Module_ID,
                *[getattr(row_number_query.c, f) for f in self._columns],
            )
            .filter(row_number_query.c.rnk == 1)
            .filter(row_number_query.c._Terminated == 0)
        )

        result = self._session.execute(final_query)
        return result

    def _get_object_query(self):
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
            .filter(ObjectsTable.Start_Validity < self._valid_timepoint)
        )

        # Inner filters
        if self._filter_object_types:
            subq = subq.filter(ObjectsTable.Object_Type.in_(self._filter_object_types))
        if self._filter_codes:
            subq = subq.filter(ObjectsTable.Code.in_(self._filter_codes))

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(
                literal(0).label("Module_ID"),
                literal(0).label("_Terminated"),
                *[getattr(aliased_objects, f) for f in self._columns],
            )
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity >= self._valid_timepoint,
                    subq.c.End_Validity.is_(None),
                )
            )
            .order_by(desc(subq.c.Modified_Date))
        )
        return stmt

    def _get_module_object_query(self):
        query = (
            select(
                ModuleObjectsTable,
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.Code,
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
                case((ModuleObjectContextTable.Action == "Terminate", 1), else_=0).label("_Terminated"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleObjectsTable.ModuleObjectContext)
            .filter(ModuleObjectsTable.Modified_Date < self._module_timepoint)
            .filter(ModuleObjectContextTable.Hidden == False)
        )

        # Inner filters
        if self._filter_module_id:
            query = query.filter(ModuleObjectsTable.Module_ID == self._filter_module_id)
        if self._filter_object_types:
            query = query.filter(ModuleObjectsTable.Object_Type.in_(self._filter_object_types))
        if self._filter_codes:
            query = query.filter(ModuleObjectsTable.Code.in_(self._filter_codes))

        subq = query.subquery()

        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = (
            select(
                aliased_objects.Module_ID,
                subq.c._Terminated,
                *[getattr(aliased_objects, f) for f in self._columns],
            )
            .filter(subq.c._RowNumber == 1)
            .filter(subq.c.Deleted == False)
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
