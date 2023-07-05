from copy import deepcopy
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.orm import aliased
from sqlalchemy.orm.session import make_transient
from sqlalchemy.sql import and_

from app.dynamic.repository.repository import BaseRepository
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.models.models import ModuleStatusCode


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

    def get_objects_in_time(self, module_id: int, before: datetime) -> List[ModuleObjectsTable]:
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
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Modified_Date < before)
            .subquery()
        )

        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1).filter(subq.c.Deleted == False)

        objects: List[ModuleObjectsTable] = self._db.execute(stmt).scalars()
        return objects

    @staticmethod
    def latest_versions_query(
        code: str,
        status_filter: Optional[List[str]] = None,
        is_active: bool = True,
    ):
        """
        Fetches a list of all latest module versions in progress
        for a valid object. returns 1 module object per module.
        """
        subq = (
            select(
                ModuleObjectsTable,
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.Module_ID,
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleTable)
        )

        filters = [ModuleObjectsTable.Code == code]
        if is_active:
            filters.append(ModuleTable.is_active)  # Closed false + Activated true
        if status_filter is not None:
            filters.append(ModuleTable.Current_Status.in_(status_filter))
        if len(filters) > 0:
            subq = subq.filter(and_(*filters))

        subq = subq.subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1).order_by(desc(subq.c.Modified_Date))
        return stmt

    def get_latest_per_module(
        self,
        code: str,
        minimum_status: Optional[ModuleStatusCode] = None,
        is_active: bool = True,
    ) -> List[ModuleObjectsTable]:
        # TODO: move param logic to dependency
        status_list = None
        if minimum_status is not None:
            status_list = ModuleStatusCode.after(minimum_status)

        query = self.latest_versions_query(code=code, status_filter=status_list, is_active=is_active)
        return self.fetch_all(query)

    @staticmethod
    def all_latest_query(
        only_active_modules: bool = True,
        status_filter: Optional[List[str]] = None,
        owner_uuid: Optional[UUID] = None,
    ):
        """
        Fetches a list of all latest module versions in progress
        for a valid object. returns 1 module object per module.
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
        )

        filters = []
        if only_active_modules:
            filters.append(ModuleTable.is_active)  # Closed false + Activated true
        if status_filter is not None:
            filters.append(ModuleTable.Current_Status.in_(status_filter))
        if owner_uuid is not None:
            filters.append(ModuleTable.is_manager(user_uuid=owner_uuid))

        if len(filters) > 0:
            subq = subq.filter(and_(*filters))

        subq = subq.subquery()
        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = select(aliased_objects).filter(subq.c._RowNumber == 1).order_by(desc(subq.c.Modified_Date))
        return stmt

    def get_all_latest(
        self,
        only_active_modules: bool = True,
        minimum_status: Optional[ModuleStatusCode] = None,
        owner_uuid: Optional[UUID] = None,
    ) -> List[ModuleObjectsTable]:
        # TODO: move param logic to dependency
        status_list = None
        if minimum_status is not None:
            status_list = ModuleStatusCode.after(minimum_status)

        query = self.all_latest_query(
            only_active_modules=only_active_modules,
            status_filter=status_list,
            owner_uuid=owner_uuid,
        )
        return self.fetch_all(query)

    def patch_latest_module_object(
        self,
        module_id: int,
        object_type: str,
        object_id: int,
        changes: dict,
        timepoint: datetime,
        by_uuid: UUID,
    ) -> ModuleObjectsTable:
        record: Optional[ModuleObjectsTable] = self.get_latest_by_id(
            module_id,
            object_type,
            object_id,
        )
        if not record:
            raise ValueError(f"lineage_id does not exist in this module")

        new_record: ModuleObjectsTable = self.patch_module_object(
            record,
            changes,
            timepoint,
            by_uuid,
        )
        return new_record

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

        for key, value in changes.items():
            setattr(record, key, value)

        record.UUID = uuid4()
        record.Adjust_On = previous_uuid
        record.Modified_Date = timepoint
        record.Modified_By_UUID = by_uuid

        return record
