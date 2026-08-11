import uuid
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
    owner_uuid: uuid.UUID


class ModuleObjectRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuid: UUID) -> ModuleObjectsTable | None:
        stmt = select(ModuleObjectsTable).filter(ModuleObjectsTable.UUID == uuid)
        return self.fetch_first(session, stmt)

    def get_by_object_type_and_uuid(self, session: Session, object_type: str, uuid: UUID) -> ModuleObjectsTable | None:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.UUID == uuid)
            .filter(ModuleObjectsTable.Object_Type == object_type)
        )
        return self.fetch_first(session, stmt)

    def get_by_module_id_object_type_and_uuid(
        self,
        session: Session,
        module_id: int,
        object_type: str,
        uuid: UUID,
    ) -> ModuleObjectsTable | None:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.UUID == uuid)
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Object_Type == object_type)
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
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Code == object_code)
            .order_by(desc(ModuleObjectsTable.Modified_Date))
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
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Object_Type == object_type)
            .filter(ModuleObjectsTable.Object_ID == object_id)
            .order_by(desc(ModuleObjectsTable.Modified_Date))
        )
        return self.fetch_first(session, stmt)

    def _build_snapshot_objects_query(self, module_id: int, before: datetime):
        return (
            select(
                ModuleObjectsTable,
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.Code,
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleObjectsTable.ModuleObjectContext)
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Modified_Date < before)
            .filter(ModuleObjectContextTable.Hidden == False)
        )

    def get_objects_in_time(self, session: Session, module_id: int, before: datetime) -> list[ModuleObjectsTable]:
        subq = self._build_snapshot_objects_query(module_id, before).subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1).filter(subq.c.Deleted == False)

        objects: list[ModuleObjectsTable] = session.execute(stmt).scalars()
        return objects

    def get_all_objects_in_time(self, session: Session, module_id: int, before: datetime) -> list[ModuleObjectsTable]:
        subq = self._build_snapshot_objects_query(module_id, before).subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1).filter(subq.c.Deleted == False)

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
                ModuleObjectContextTable.Action.label("context_action"),
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.Module_ID,
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleTable)
            .join(ModuleObjectsTable.ModuleObjectContext)
            .filter(ModuleObjectContextTable.Hidden == False)
        )

        filters = [ModuleObjectsTable.Code == code]
        if is_active:
            filters.append(ModuleTable.is_active)  # Closed false + Activated true
        if status_filter is not None:
            # Subquery for the latest status per module
            module_status_subq = select(
                ModuleStatusHistoryTable.Module_ID,
                ModuleStatusHistoryTable.Status,
                func.row_number()
                .over(partition_by=ModuleStatusHistoryTable.Module_ID, order_by=desc(ModuleStatusHistoryTable.ID))
                .label("_StatusRowNumber"),
            ).subquery()
            # Update main query to include status subquery join
            subq = subq.join(
                module_status_subq,
                and_(
                    ModuleTable.Module_ID == module_status_subq.c.Module_ID, module_status_subq.c._StatusRowNumber == 1
                ),
            )
            # Apply status filter
            filters.append(module_status_subq.c.Status.in_(status_filter))

        if len(filters) > 0:
            subq = subq.filter(and_(*filters))

        subq = subq.subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        aliased_module = aliased(ModuleTable, subq)
        stmt = (
            select(aliased_objects, aliased_module, subq.c.context_action)
            .filter(subq.c._RowNumber == 1)
            .order_by(desc(subq.c.Modified_Date))
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
            select(ModuleStatusHistoryTable.Status)
            .filter(ModuleObjectsTable.Module_ID == ModuleStatusHistoryTable.Module_ID)
            .order_by(ModuleStatusHistoryTable.ID.desc())
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
                    partition_by=ModuleObjectsTable.Code,
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
                latest_status_subquery,  # Include each mo latest status
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleTable)
            .join(ModuleObjectsTable.ObjectStatics)
            .join(ModuleObjectsTable.ModuleObjectContext)
            .filter(ModuleObjectContextTable.Hidden == False)
        )
        # Build minimum status list starting at given status, if provided
        status_filter = ModuleStatusCode.after(minimum_status) if minimum_status is not None else None

        if module_id is not None:
            subq = subq.filter(ModuleObjectsTable.Module_ID == module_id)
        if only_active_modules:
            if module_id is not None:
                subq = subq.filter(ModuleTable.Closed == False)
            else:
                subq = subq.filter(ModuleTable.is_active)
        if status_filter is not None:
            subq = subq.filter(ModuleTable.Current_Status.in_(status_filter))
        match owner_filter:
            case OwnerFilter(is_mine=True, owner_uuid=mine):
                subq = subq.filter(
                    or_(
                        ObjectStaticsTable.Owner_1_UUID == mine,
                        ObjectStaticsTable.Owner_2_UUID == mine,
                    ).self_group()
                )
            case OwnerFilter(is_mine=False, owner_uuid=others):
                subq = subq.filter(
                    and_(
                        ObjectStaticsTable.Owner_1_UUID.is_distinct_from(others),
                        ObjectStaticsTable.Owner_2_UUID.is_distinct_from(others),
                    ).self_group()
                )
        if object_types:
            subq = subq.filter(ModuleObjectsTable.Object_Type.in_(object_types))
        if actions:
            subq = subq.filter(ModuleObjectContextTable.Action.in_(actions))

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
                    aliased_module_object_context.Action,
                    aliased_module_object_context.Original_Adjust_On,
                )
            )
            .filter(subq.c._RowNumber == 1)
            .filter(subq.c.Deleted == False)
        )

        # This field changes per record and must therefor be compared after gaining the newest record
        if title is not None:
            stmt = stmt.filter(subq.c.Title.like(title))

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
        by_uuid: UUID,
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
            by_uuid,
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
        previous_uuid: UUID = deepcopy(record.UUID)

        # Release the object from sqlalchemy so we can use it as the base of a new object
        session.expunge(record)
        make_transient(record)

        new_record = deepcopy(record)
        for key, value in changes.items():
            setattr(new_record, key, value)

        new_record.UUID = uuid4()
        new_record.Adjust_On = previous_uuid
        new_record.Modified_Date = timepoint
        new_record.Modified_By_UUID = by_uuid

        return new_record

    def confirm_accessible_object_codes(self, session: Session, module_id: int, object_codes: set[str]) -> set[str]:
        if not object_codes:
            return object_codes

        # "Vigerend" in objects table
        timepoint: datetime = datetime.now(UTC)
        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.Code,
                order_by=desc(ObjectsTable.Modified_Date),
            )
            .label("_RowNumber")
        )
        subq = (
            select(ObjectsTable.Code, ObjectsTable.End_Validity, row_number)
            .filter(ObjectsTable.Code.in_(object_codes))
            .filter(ObjectsTable.Start_Validity <= timepoint)
            .subquery()
        )
        vigerend_codes = (
            select(
                subq.c.Code,
                literal(0).label("Priority"),
                literal(1).label("Usable"),
            )
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > timepoint,
                    subq.c.End_Validity.is_(None),
                )
            )
        )

        # Module objects
        # @note: Objects set to be terminated by the module should not be allowed to be used
        #   Because they wont exist anymore when the module is completed
        module_codes = (
            select(
                ModuleObjectContextTable.Code,
                literal(1).label("Priority"),
                case(
                    # To be clear; we return the row here with Usable = 0 when the object is terminated
                    # This will force this record to be picked in the merge/group below
                    # This allows us to not allow this code
                    (ModuleObjectContextTable.Action == ModuleObjectActionFull.Terminate.value, 0),
                    else_=1,
                ).label("Usable"),
            )
            .filter(ModuleObjectContextTable.Module_ID == module_id)
            .filter(ModuleObjectContextTable.Code.in_(object_codes))
            .filter(ModuleObjectContextTable.Hidden == False)
        )

        codes = vigerend_codes.union_all(module_codes).subquery()
        highest_priority_per_code = select(
            codes.c.Code,
            codes.c.Usable,
            func.row_number()
            .over(
                partition_by=codes.c.Code,
                order_by=desc(codes.c.Priority),
            )
            .label("_RowNumber"),
        ).subquery()
        stmt = (
            select(highest_priority_per_code.c.Code)
            .filter(highest_priority_per_code.c._RowNumber == 1)
            .filter(highest_priority_per_code.c.Usable == 1)
        )

        return set(session.execute(stmt).scalars())
