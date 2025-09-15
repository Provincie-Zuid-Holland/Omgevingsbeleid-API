from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, aliased
from sqlalchemy.orm.session import make_transient
from sqlalchemy.sql import Select, and_, or_

from app.api.base_repository import BaseRepository
from app.api.domains.modules.types import ModuleObjectActionFull, ModuleStatusCode
from app.api.utils.pagination import SortedPagination
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable
from app.core.tables.objects import ObjectStaticsTable


@dataclass
class LatestObjectPerModuleResult:
    module_object: ModuleObjectsTable
    module: ModuleTable
    context_action: ModuleObjectActionFull


class ModuleObjectRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuid: UUID) -> Optional[ModuleObjectsTable]:
        stmt = select(ModuleObjectsTable).filter(ModuleObjectsTable.UUID == uuid)
        return self.fetch_first(session, stmt)

    def get_by_object_type_and_uuid(
        self, session: Session, object_type: str, uuid: UUID
    ) -> Optional[ModuleObjectsTable]:
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
    ) -> Optional[ModuleObjectsTable]:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.UUID == uuid)
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Object_Type == object_type)
        )
        return self.fetch_first(session, stmt)

    def get_latest_by_id(
        self,
        session: Session,
        module_id: int,
        object_type: str,
        object_id: int,
    ) -> Optional[ModuleObjectsTable]:
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

    def get_objects_in_time(self, session: Session, module_id: int, before: datetime) -> List[ModuleObjectsTable]:
        subq = self._build_snapshot_objects_query(module_id, before).subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1).filter(subq.c.Deleted == False)

        objects: List[ModuleObjectsTable] = session.execute(stmt).scalars()
        return objects

    def get_all_objects_in_time(self, session: Session, module_id: int, before: datetime) -> List[ModuleObjectsTable]:
        subq = self._build_snapshot_objects_query(module_id, before).subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1).filter(subq.c.Deleted == False)

        objects: List[ModuleObjectsTable] = session.execute(stmt).all()
        return objects

    def _latest_per_module_query(
        self,
        code: str,
        status_filter: Optional[List[str]] = None,
        is_active: bool = True,
    ) -> Select[Tuple[ModuleObjectsTable, ModuleTable, ModuleObjectActionFull]]:
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
        minimum_status: Optional[ModuleStatusCode] = None,
        is_active: bool = True,
    ) -> List[LatestObjectPerModuleResult]:
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
        minimum_status: Optional[ModuleStatusCode] = None,
        owner_uuid: Optional[UUID] = None,
        object_type: Optional[str] = None,
        title: Optional[str] = None,
        actions: List[ModuleObjectActionFull] = [],
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

        # Build filter list
        filters = [
            ModuleTable.is_active if only_active_modules else None,
            ModuleTable.Current_Status.in_(status_filter) if status_filter is not None else None,
            (
                or_(
                    ObjectStaticsTable.Owner_1_UUID == owner_uuid,
                    ObjectStaticsTable.Owner_2_UUID == owner_uuid,
                ).self_group()
                if owner_uuid is not None
                else None
            ),
            ModuleObjectsTable.Object_Type == object_type if object_type is not None else None,
            ModuleObjectsTable.Title.like(title) if title is not None else None,
            ModuleObjectContextTable.Action.in_(actions) if actions else None,
        ]

        # Applying your filters and making it a subquery
        subq = subq.filter(and_(*[f for f in filters if f is not None])).subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)

        # Outer query to select all fields including the latest status
        stmt = select(aliased_objects, subq.c.Latest_Status).filter(subq.c._RowNumber == 1)

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
    ) -> Tuple[ModuleObjectsTable, ModuleObjectsTable]:
        old_record: Optional[ModuleObjectsTable] = self.get_latest_by_id(
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
