from copy import deepcopy
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session, aliased
from sqlalchemy.orm.session import make_transient

from app.extensions.modules.db.module_objects_table import ModuleObjectsTable


class ModuleObjectRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_by_uuid(self, uuid: UUID) -> Optional[ModuleObjectsTable]:
        stmt = select(ModuleObjectsTable).filter(ModuleObjectsTable.UUID == uuid)
        maybe_object = self._db.scalars(stmt).first()
        return maybe_object

    def get_by_object_type_and_uuid(
        self, object_type: str, uuid: UUID
    ) -> Optional[ModuleObjectsTable]:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.UUID == uuid)
            .filter(ModuleObjectsTable.Object_Type == object_type)
        )
        maybe_object = self._db.scalars(stmt).first()
        return maybe_object

    def get_by_module_id_object_type_and_uuid(
        self, module_id: int, object_type: str, uuid: UUID
    ) -> Optional[ModuleObjectsTable]:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.UUID == uuid)
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Object_Type == object_type)
        )
        maybe_object = self._db.scalars(stmt).first()
        return maybe_object

    def get_latest_by_id(
        self, module_id: int, object_type: str, object_id: int
    ) -> Optional[ModuleObjectsTable]:
        stmt = (
            select(ModuleObjectsTable)
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Object_Type == object_type)
            .filter(ModuleObjectsTable.Object_ID == object_id)
            .order_by(desc(ModuleObjectsTable.Modified_Date))
        )
        maybe_object = self._db.scalars(stmt).first()
        return maybe_object

    def get_objects_in_time(self, module_id: int, before: datetime) -> List[dict]:
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
        stmt = (
            select(aliased_objects)
            .filter(subq.c._RowNumber == 1)
            .filter(subq.c.Deleted == False)
        )

        rows: List[dict] = []
        for row in self._db.execute(stmt).scalars():
            dictrow = dict(row.__dict__)
            dictrow.pop("_sa_instance_state", None)
            rows.append(dictrow)

        return rows

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
