from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.orm import aliased, load_only
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
        code: str,
        minimum_status: Optional[ModuleStatusCode] = None,
        is_active: bool = True,
    ) -> List[LatestObjectPerModuleResult]:
        # Build minimum status list starting at given status, if provided
        status_filter = ModuleStatusCode.after(minimum_status) if minimum_status is not None else None
        query = self.latest_per_module_query(code=code, status_filter=status_filter, is_active=is_active)
        rows = self._db.execute(query).all()
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
        pagination: SortedPagination,
        only_active_modules: bool = True,
        minimum_status: Optional[ModuleStatusCode] = None,
        owner_uuid: Optional[UUID] = None,
        object_type: Optional[str] = None,
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
            ModuleObjectContextTable.Action.in_(actions) if actions else None,
        ]

        # Applying your filters and making it a subquery
        subq = subq.filter(and_(*[f for f in filters if f is not None])).subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)

        # Outer query to select all fields including the latest status
        stmt = select(aliased_objects, subq.c.Latest_Status).filter(subq.c._RowNumber == 1)

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

    def get_latest_versions_by_werkingsgebied(self, werkingsgebied_code: str) -> List[LatestObjectPerModuleResult]:
        subq = (
            select(
                ModuleObjectsTable,
                ModuleTable,
                ModuleObjectContextTable.Action.label("context_action"),
                func.row_number()
                .over(
                    partition_by=(ModuleObjectsTable.Module_ID, ModuleObjectsTable.Code),
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .options(
                load_only(
                    ModuleObjectsTable.UUID,
                    ModuleObjectsTable.Object_ID,
                    ModuleObjectsTable.Object_Type,
                    ModuleObjectsTable.Title,
                    ModuleObjectsTable.Code,
                    ModuleObjectsTable.Werkingsgebied_Code,
                    ModuleObjectsTable.Modified_Date,
                ),
                load_only(
                    ModuleTable.Module_ID,
                    ModuleTable.Title,
                ),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleTable, ModuleObjectsTable.Module_ID == ModuleTable.Module_ID)
            .join(
                ModuleObjectContextTable,
                and_(
                    ModuleObjectsTable.Module_ID == ModuleObjectContextTable.Module_ID,
                    ModuleObjectsTable.Code == ModuleObjectContextTable.Code,
                ),
            )
            .where(ModuleTable.Activated == 1)
            .where(ModuleTable.Closed == 0)
            .where(ModuleObjectContextTable.Action != ModuleObjectActionFull.Terminate)
            .where(ModuleObjectContextTable.Hidden == False)
        ).subquery("LatestModuleObjects")

        aliased_mo = aliased(ModuleObjectsTable, subq)
        aliased_mod = aliased(ModuleTable, subq)
        context_action_col = subq.c.context_action

        stmt = (
            select(aliased_mo, aliased_mod, context_action_col)
            .where(subq.c._RowNumber == 1)
            .where(subq.c.Werkingsgebied_Code == werkingsgebied_code)
            .order_by(desc(subq.c.Modified_Date))
        )

        rows = self._db.execute(stmt).all()
        return [
            LatestObjectPerModuleResult(
                module_object=row[0],
                module=row[1],
                context_action=row[2],
            )
            for row in rows
        ]

    @staticmethod
    def public_revisions_per_module_query(code: str, allowed_status_list: List[str]):
        """
        view of latest public revisions per module, but instead of excluding concept versions
        it shows the last available public status.
        """
        # group public statuses per module
        latest_status_subq = (
            select(
                ModuleStatusHistoryTable,
                ModuleTable.Title,
                func.row_number()
                .over(partition_by=ModuleStatusHistoryTable.Module_ID, order_by=desc(ModuleStatusHistoryTable.ID))
                .label("_StatusRowNumber"),
            )
            .join(ModuleStatusHistoryTable.Module)
            .filter(ModuleTable.is_active, ModuleStatusHistoryTable.Status.in_(allowed_status_list))
            .subquery("latest_status_subq")
        )

        # rank latest mod objects for this status
        module_objects_filtered_subq = (
            select(
                ModuleObjectsTable.Module_ID,
                ModuleObjectsTable.UUID,
                ModuleObjectsTable.Code,
                ModuleObjectsTable.Modified_Date,
                latest_status_subq.c.Status,
                latest_status_subq.c.Title,
                ModuleObjectContextTable.Action,
                func.row_number()
                .over(partition_by=ModuleObjectsTable.Module_ID, order_by=desc(ModuleObjectsTable.Modified_Date))
                .label("_ObjectRowNumber"),
            )
            .join(latest_status_subq, ModuleObjectsTable.Module_ID == latest_status_subq.c.Module_ID)
            .join(ModuleObjectsTable.ModuleObjectContext)
            .filter(
                latest_status_subq.c._StatusRowNumber == 1,
                ModuleObjectsTable.Modified_Date <= latest_status_subq.c.Created_Date,
                ModuleObjectContextTable.Code == code,
                ModuleObjectContextTable.Hidden == False,
            )
            .subquery("module_objects_filtered_subq")
        )

        # assemble query and pick the latest object for each module
        stmt = (
            select(
                module_objects_filtered_subq.c.Module_ID.label("Module_ID"),
                module_objects_filtered_subq.c.Title.label("Module_Title"),
                module_objects_filtered_subq.c.Status.label("Module_Object_Status"),
                module_objects_filtered_subq.c.UUID.label("Module_Object_UUID"),
                module_objects_filtered_subq.c.Action.label("Action"),
                ModuleTable.Current_Status.label("Module_Status"),
            )
            .select_from(module_objects_filtered_subq)
            .join(ModuleTable, module_objects_filtered_subq.c.Module_ID == ModuleTable.Module_ID)
            .filter(module_objects_filtered_subq.c._ObjectRowNumber == 1)
            .order_by(desc(module_objects_filtered_subq.c.Modified_Date))
        )

        return stmt
