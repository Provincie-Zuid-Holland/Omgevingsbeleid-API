from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import case, desc, func, literal, select
from sqlalchemy.orm import Session, aliased, load_only
from sqlalchemy.orm.session import make_transient
from sqlalchemy.sql import Select, and_, or_

from app.api.base_repository import BaseRepository
from app.api.domains.modules.types import ModuleObjectActionFull, ModuleStatusCode
from app.api.utils.pagination import SortedPagination
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable


@dataclass
class LatestObjectPerModuleResult:
    module_object: ModuleObjectsTable
    module: ModuleTable
    context_action: ModuleObjectActionFull


class OwnerFilter(BaseModel):
    is_mine: bool
    owner_id: UUID


class ModuleObjectRepository(BaseRepository):
    def get_by_id(self, session: Session, idx: UUID) -> ModuleObjectsTable | None:
        stmt = select(ModuleObjectsTable).filter(ModuleObjectsTable.id == idx)
        return self.fetch_first(session, stmt)

    def get_by_object_type_and_id(self, session: Session, object_type: str, idx: UUID) -> ModuleObjectsTable | None:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.id == idx)
            .filter(ModuleObjectsTable.object_type == object_type)
        )
        return self.fetch_first(session, stmt)

    def get_by_module_id_object_type_and_id(
        self,
        session: Session,
        module_id: int,
        object_type: str,
        idx: UUID,
    ) -> ModuleObjectsTable | None:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.id == idx)
            .filter(ModuleObjectsTable.module_id == module_id)
            .filter(ModuleObjectsTable.object_type == object_type)
        )
        return self.fetch_first(session, stmt)

    def get_latest_by_module_id_object_code(
        self,
        session: Session,
        module_id: int,
        object_code: str,
    ) -> ModuleObjectsTable | None:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.module_id == module_id)
            .filter(ModuleObjectsTable.code == object_code)
            .order_by(desc(ModuleObjectsTable.modified_date))
        )
        return self.fetch_first(session, stmt)

    def get_latest_by_id(
        self,
        session: Session,
        module_id: int,
        object_type: str,
        object_id: int,
    ) -> ModuleObjectsTable | None:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.module_id == module_id)
            .filter(ModuleObjectsTable.object_type == object_type)
            .filter(ModuleObjectsTable.object_id == object_id)
            .order_by(desc(ModuleObjectsTable.modified_date))
        )
        return self.fetch_first(session, stmt)

    def _build_snapshot_objects_query(self, module_id: int, before: datetime):
        return (
            select(
                ModuleObjectsTable,
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.code,
                    order_by=desc(ModuleObjectsTable.modified_date),
                )
                .label("_row_number"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleObjectsTable.module_object_context)
            .filter(ModuleObjectsTable.module_id == module_id)
            .filter(ModuleObjectsTable.modified_date < before)
            .filter(ModuleObjectContextTable.hidden == False)
        )

    def get_objects_in_time(self, session: Session, module_id: int, before: datetime) -> list[ModuleObjectsTable]:
        subq = self._build_snapshot_objects_query(module_id, before).subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._row_number == 1).filter(subq.c.deleted == False)

        objects: list[ModuleObjectsTable] = session.execute(stmt).scalars()
        return objects

    def get_all_objects_in_time(self, session: Session, module_id: int, before: datetime) -> list[ModuleObjectsTable]:
        subq = self._build_snapshot_objects_query(module_id, before).subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._row_number == 1).filter(subq.c.deleted == False)

        objects: list[ModuleObjectsTable] = session.execute(stmt).all()
        return objects

    def _latest_per_module_query(
        self,
        code: str,
        status_filter: list[str] | None = None,
        is_active: bool = True,
    ) -> Select[tuple[ModuleObjectsTable, ModuleTable, ModuleObjectActionFull]]:
        """
        Fetch the latest module object versions grouped by
        every module containing it. used e.g. to list any
        active draft versions of an existing valid object.
        """
        subq = (
            select(
                ModuleObjectsTable,
                ModuleTable,
                ModuleObjectContextTable.action.label("context_action"),
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.module_id,
                    order_by=desc(ModuleObjectsTable.modified_date),
                )
                .label("_row_number"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleTable)
            .join(ModuleObjectsTable.module_object_context)
            .filter(ModuleObjectContextTable.hidden == False)
        )

        filters = [ModuleObjectsTable.code == code]
        if is_active:
            filters.append(ModuleTable.is_active)  # closed false + activated true
        if status_filter is not None:
            # Subquery for the latest status per module
            module_status_subq = select(
                ModuleStatusHistoryTable.module_id,
                ModuleStatusHistoryTable.status,
                func.row_number()
                .over(partition_by=ModuleStatusHistoryTable.module_id, order_by=desc(ModuleStatusHistoryTable.id))
                .label("_status_row_number"),
            ).subquery()
            # Update main query to include status subquery join
            subq = subq.join(
                module_status_subq,
                and_(
                    ModuleTable.module_id == module_status_subq.c.module_id,
                    module_status_subq.c._status_row_number == 1,
                ),
            )
            # Apply status filter
            filters.append(module_status_subq.c.status.in_(status_filter))

        if len(filters) > 0:
            subq = subq.filter(and_(*filters))

        subq = subq.subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        aliased_module = aliased(ModuleTable, subq)
        stmt = (
            select(aliased_objects, aliased_module, subq.c.context_action)
            .filter(subq.c._row_number == 1)
            .order_by(desc(subq.c.modified_date))
        )
        return stmt

    def get_latest_per_module(
        self,
        session: Session,
        code: str,
        minimum_status: ModuleStatusCode | None = None,
        is_active: bool = True,
    ) -> list[LatestObjectPerModuleResult]:
        # Build minimum status list starting at given status, if provided
        status_filter = ModuleStatusCode.after(minimum_status) if minimum_status is not None else None
        query = self._latest_per_module_query(code=code, status_filter=status_filter, is_active=is_active)
        rows = session.execute(query).all()
        named_results = [
            LatestObjectPerModuleResult(
                module_object=row[0],
                module=row[1],
                context_action=row[2],
            )
            for row in rows
        ]
        return named_results

    def get_all_latest(
        self,
        session: Session,
        pagination: SortedPagination,
        only_active_modules: bool = True,
        minimum_status: ModuleStatusCode | None = None,
        owner_filter: OwnerFilter | None = None,
        object_types: Sequence[str] = (),
        title: str | None = None,
        actions: Sequence[ModuleObjectActionFull] = (),
        module_id: int | None = None,
    ):
        """
        Generic filterable module-object listing query used
        for listing objects in draft or if object type is unknown.
        """
        latest_status_subquery = (
            select(ModuleStatusHistoryTable.status)
            .filter(ModuleObjectsTable.module_id == ModuleStatusHistoryTable.module_id)
            .order_by(ModuleStatusHistoryTable.id.desc())
            .limit(1)
            .correlate(ModuleObjectsTable)  # Explicit correlate needed to merge back in outer query
            .scalar_subquery()
            .label("Latest_Status")
        )

        subq = (
            select(
                ModuleObjectsTable,
                ModuleObjectContextTable,
                ObjectStaticsTable,
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.code,
                    order_by=desc(ModuleObjectsTable.modified_date),
                )
                .label("_row_number"),
                latest_status_subquery,  # Include each mo latest status
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleTable)
            .join(ModuleObjectsTable.object_statics)
            .join(ModuleObjectsTable.module_object_context)
            .filter(ModuleObjectContextTable.hidden == False)
        )
        # Build minimum status list starting at given status, if provided
        status_filter = ModuleStatusCode.after(minimum_status) if minimum_status is not None else None

        if module_id is not None:
            subq = subq.filter(ModuleObjectsTable.module_id == module_id)
        if only_active_modules:
            if module_id is not None:
                subq = subq.filter(ModuleTable.closed == False)
            else:
                subq = subq.filter(ModuleTable.is_active)
        if status_filter is not None:
            subq = subq.filter(ModuleTable.current_status.in_(status_filter))
        match owner_filter:
            case OwnerFilter(is_mine=True, owner_id=mine):
                subq = subq.filter(
                    or_(
                        ObjectStaticsTable.owner_1_id == mine,
                        ObjectStaticsTable.owner_2_id == mine,
                    ).self_group()
                )
            case OwnerFilter(is_mine=False, owner_id=others):
                subq = subq.filter(
                    and_(
                        ObjectStaticsTable.owner_1_id.is_distinct_from(others),
                        ObjectStaticsTable.owner_2_id.is_distinct_from(others),
                    ).self_group()
                )
        if object_types:
            subq = subq.filter(ModuleObjectsTable.object_type.in_(object_types))
        if actions:
            subq = subq.filter(ModuleObjectContextTable.action.in_(actions))

        subq = subq.subquery()

        aliased_objects = aliased(ModuleObjectsTable, subq)
        aliased_object_statics = aliased(ObjectStaticsTable, subq)
        aliased_module_object_context = aliased(ModuleObjectContextTable, subq)

        stmt = (
            select(
                aliased_objects,
                aliased_object_statics,
                aliased_module_object_context,
                subq.c.Latest_Status,
            )
            .options(
                load_only(
                    aliased_module_object_context.action,
                    aliased_module_object_context.original_adjust_on,
                )
            )
            .filter(subq.c._row_number == 1)
            .filter(subq.c.deleted == False)
        )

        # This field changes per record and must therefor be compared after gaining the newest record
        if title is not None:
            stmt = stmt.filter(subq.c.title.like(title))

        return self.fetch_paginated_no_scalars(
            session=session,
            statement=stmt,
            limit=pagination.limit,
            offset=pagination.offset,
            sort=(getattr(subq.c, pagination.sort.column), pagination.sort.order),
        )

    def patch_latest_module_object(
        self,
        session: Session,
        module_id: int,
        object_type: str,
        object_id: int,
        changes: dict,
        timepoint: datetime,
        by_id: UUID,
    ) -> tuple[ModuleObjectsTable, ModuleObjectsTable]:
        old_record: ModuleObjectsTable | None = self.get_latest_by_id(
            session,
            module_id,
            object_type,
            object_id,
        )
        if not old_record:
            raise ValueError("lineage_id does not exist in this module")

        new_record: ModuleObjectsTable = self.patch_module_object(
            session,
            old_record,
            changes,
            timepoint,
            by_id,
        )
        return old_record, new_record

    def patch_module_object(
        self,
        session: Session,
        record: ModuleObjectsTable,
        changes: dict,
        timepoint: datetime,
        by_uuid: UUID,
    ) -> ModuleObjectsTable:
        previous_uuid: UUID = deepcopy(record.id)

        # Release the object from sqlalchemy so we can use it as the base of a new object
        session.expunge(record)
        make_transient(record)

        new_record = deepcopy(record)
        for key, value in changes.items():
            setattr(new_record, key, value)

        new_record.id = uuid4()
        new_record.adjust_on = previous_uuid
        new_record.modified_date = timepoint
        new_record.modified_by_id = by_uuid

        return new_record

    def confirm_accessible_object_codes(self, session: Session, module_id: int, object_codes: set[str]) -> set[str]:
        if not object_codes:
            return object_codes

        # "Vigerend" in objects table
        timepoint: datetime = datetime.now(UTC)
        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.code,
                order_by=desc(ObjectsTable.modified_date),
            )
            .label("_row_number")
        )
        subq = (
            select(ObjectsTable.code, ObjectsTable.end_validity, row_number)
            .filter(ObjectsTable.code.in_(object_codes))
            .filter(ObjectsTable.start_validity <= timepoint)
            .subquery()
        )
        vigerend_codes = (
            select(
                subq.c.code,
                literal(0).label("Priority"),
                literal(1).label("Usable"),
            )
            .filter(subq.c._row_number == 1)
            .filter(
                or_(
                    subq.c.end_validity > timepoint,
                    subq.c.end_validity.is_(None),
                )
            )
        )

        # Module objects
        # @note: Objects set to be terminated by the module should not be allowed to be used
        #   Because they won't exist anymore when the module is completed
        module_codes = (
            select(
                ModuleObjectContextTable.code,
                literal(1).label("Priority"),
                case(
                    # To be clear: we return the row here with Usable = 0 when the object is terminated
                    # This will force this record to be picked in the merge/group step below
                    # This allows us to reject this code
                    (ModuleObjectContextTable.action == ModuleObjectActionFull.Terminate.value, 0),
                    else_=1,
                ).label("Usable"),
            )
            .filter(ModuleObjectContextTable.module_id == module_id)
            .filter(ModuleObjectContextTable.code.in_(object_codes))
            .filter(ModuleObjectContextTable.hidden == False)
        )

        codes = vigerend_codes.union_all(module_codes).subquery()
        highest_priority_per_code = select(
            codes.c.code,
            codes.c.Usable,
            func.row_number()
            .over(
                partition_by=codes.c.code,
                order_by=desc(codes.c.Priority),
            )
            .label("_row_number"),
        ).subquery()
        stmt = (
            select(highest_priority_per_code.c.code)
            .filter(highest_priority_per_code.c._row_number == 1)
            .filter(highest_priority_per_code.c.Usable == 1)
        )

        return set(session.execute(stmt).scalars())
