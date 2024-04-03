from copy import deepcopy
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import Result, desc, func, select
from sqlalchemy.orm import aliased
from sqlalchemy.orm.session import make_transient
from sqlalchemy.sql import and_, or_

from app.dynamic.db import ObjectStaticsTable
from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import SortedPagination
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.models.models import ModuleObjectActionFilter, ModuleStatusCode


class ModuleObjectRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[ModuleObjectsTable]:
        stmt = select(ModuleObjectsTable).filter(ModuleObjectsTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_by_object_type_and_uuid(self, object_type: str, uuid: UUID) -> Optional[ModuleObjectsTable]:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.UUID == uuid)
            .filter(ModuleObjectsTable.Object_Type == object_type)
        )
        return self.fetch_first(stmt)

    def get_by_module_id_object_type_and_uuid(
        self, module_id: int, object_type: str, uuid: UUID
    ) -> Optional[ModuleObjectsTable]:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.UUID == uuid)
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Object_Type == object_type)
        )
        return self.fetch_first(stmt)

    def get_latest_by_id(self, module_id: int, object_type: str, object_id: int) -> Optional[ModuleObjectsTable]:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Object_Type == object_type)
            .filter(ModuleObjectsTable.Object_ID == object_id)
            .order_by(desc(ModuleObjectsTable.Modified_Date))
        )
        return self.fetch_first(stmt)

    @staticmethod
    def _build_snapshot_objects_query(module_id: int, before: datetime):
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

    def get_objects_in_time(self, module_id: int, before: datetime) -> List[ModuleObjectsTable]:
        subq = self._build_snapshot_objects_query(module_id, before).subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1).filter(subq.c.Deleted == False)

        objects: List[ModuleObjectsTable] = self._db.execute(stmt).scalars()
        return objects

    def get_all_objects_in_time(self, module_id: int, before: datetime) -> List[ModuleObjectsTable]:
        subq = self._build_snapshot_objects_query(module_id, before).subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1).filter(subq.c.Deleted == False)

        objects: List[ModuleObjectsTable] = self._db.execute(stmt).all()
        return objects

    @staticmethod
    def latest_per_module_query(
        code: str,
        status_filter: Optional[List[str]] = None,
        is_active: bool = True,
    ):
        """
        Fetch the latest module object versions grouped by
        every module containing it. used e.g. to list any
        active draft versions of an existing valid object.
        """
        subq = (
            select(
                ModuleObjectsTable,
                ModuleTable,
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
            select(aliased_objects, aliased_module).filter(subq.c._RowNumber == 1).order_by(desc(subq.c.Modified_Date))
        )
        return stmt

    def get_latest_per_module(
        self,
        code: str,
        minimum_status: Optional[ModuleStatusCode] = None,
        is_active: bool = True,
    ) -> Result[Tuple[ModuleObjectsTable, ModuleTable]]:
        # Build minimum status list starting at given status, if provided
        status_filter = ModuleStatusCode.after(minimum_status) if minimum_status is not None else None
        query = self.latest_per_module_query(code=code, status_filter=status_filter, is_active=is_active)
        return self._db.execute(query)  # execute raw to allow tuple return object + module

    def get_all_latest(
        self,
        pagination: SortedPagination,
        only_active_modules: bool = True,
        minimum_status: Optional[ModuleStatusCode] = None,
        owner_uuid: Optional[UUID] = None,
        object_type: Optional[str] = None,
        actions: List[ModuleObjectActionFilter] = [],
    ):
        """
        Generic filterable listing of latest module-object versions
        fetched grouped per object Code.
        """
        subq = (
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
            ModuleObjectContextTable.Action.in_(actions) if actions else None,
        ]
        filters = [f for f in filters if f is not None]  # first remove None filters
        subq = subq.filter(and_(*filters))  # apply remaining filters to the query

        subq = subq.subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        aliased_module = aliased(ModuleTable, subq)

        # Select module-objects + current module status
        stmt = select(aliased_objects, aliased_module.Current_Status).filter(subq.c._RowNumber == 1)

        return self.fetch_paginated_no_scalars(
            statement=stmt,
            limit=pagination.limit,
            offset=pagination.offset,
            sort=(getattr(subq.c, pagination.sort.column), pagination.sort.order),
        )

    def patch_latest_module_object(
        self,
        module_id: int,
        object_type: str,
        object_id: int,
        changes: dict,
        timepoint: datetime,
        by_uuid: UUID,
    ) -> Tuple[ModuleObjectsTable, ModuleObjectsTable]:
        old_record: Optional[ModuleObjectsTable] = self.get_latest_by_id(
            module_id,
            object_type,
            object_id,
        )
        if not old_record:
            raise ValueError(f"lineage_id does not exist in this module")

        new_record: ModuleObjectsTable = self.patch_module_object(
            old_record,
            changes,
            timepoint,
            by_uuid,
        )
        return old_record, new_record

    def patch_module_object(
        self,
        record: ModuleObjectsTable,
        changes: dict,
        timepoint: datetime,
        by_uuid: UUID,
    ) -> ModuleObjectsTable:
        previous_uuid: UUID = deepcopy(record.UUID)

        # Release the object from sqlalchemy so we can use it as the base of a new object
        self._db.expunge(record)
        make_transient(record)

        new_record = deepcopy(record)
        for key, value in changes.items():
            setattr(new_record, key, value)

        new_record.UUID = uuid4()
        new_record.Adjust_On = previous_uuid
        new_record.Modified_Date = timepoint
        new_record.Modified_By_UUID = by_uuid

        return new_record
