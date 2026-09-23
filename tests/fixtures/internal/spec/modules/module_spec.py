from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from app.core.db.base import Base
from app.core.tables.modules import ModuleTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import BasePersistHandler, Link, PersistContext, PrimaryKey, Record, Spec


class ModuleSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {
        "created_by_id",
        "modified_by_id",
        "Module_Manager_1_UUID",
        "Module_Manager_2_UUID",
    }

    Module_ID: int

    # Sensible defaults for most cases
    Activated: bool = True
    Closed: bool = False
    Successful: bool = False
    Temporary_Locked: bool = False

    Title: str
    Description: str
    Module_Manager_1_UUID: Link | None = None
    Module_Manager_2_UUID: Link | None = None

    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        return self.Module_ID


class ModulePrefillHandler(BasePrefillHandler[ModuleSpec]):
    def fill(self, record: Record[ModuleSpec], context: PrefillContext) -> Record[ModuleSpec]:
        record = super().fill(record, context)

        return record


class ModulePersistHandler(BasePersistHandler[ModuleSpec]):
    def to_rows(self, record: Record[ModuleSpec], context: PersistContext) -> Sequence[Base]:
        spec: ModuleSpec = record.spec
        return [
            ModuleTable(
                Module_ID=spec.Module_ID,
                Activated=spec.Activated,
                Closed=spec.Closed,
                Successful=spec.Successful,
                Temporary_Locked=spec.Temporary_Locked,
                Title=spec.Title,
                Description=spec.Description,
                Module_Manager_1_UUID=spec.Module_Manager_1_UUID,
                Module_Manager_2_UUID=spec.Module_Manager_2_UUID,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                modified_date=spec.modified_date,
                modified_by_id=spec.modified_by_id,
            ),
        ]
