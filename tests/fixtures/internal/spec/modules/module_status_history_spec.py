from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from app.core.db.base import Base
from app.core.tables.modules import ModuleStatusHistoryTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import BasePersistHandler, Link, PersistContext, PrimaryKey, Record, Spec


class ModuleStatusHistorySpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"Created_By_UUID"}

    ID: int | None = None
    Module_ID: int | None = None
    Status: str | None = None

    Created_Date: datetime | None = None
    Created_By_UUID: Link | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.ID, "ID is not set which is expected to happen at this stage."
        return self.ID


class ModuleStatusHistoryPrefillHandler(BasePrefillHandler[ModuleStatusHistorySpec]):
    def fill(self, record: Record[ModuleStatusHistorySpec], context: PrefillContext) -> Record[ModuleStatusHistorySpec]:
        record = super().fill(record, context)

        if record.spec.ID is None:
            record.spec.ID = context.spec_count

        return record


class ModuleStatusHistoryPersistHandler(BasePersistHandler[ModuleStatusHistorySpec]):
    def to_rows(self, record: Record[ModuleStatusHistorySpec], context: PersistContext) -> Sequence[Base]:
        spec: ModuleStatusHistorySpec = record.spec
        return [
            ModuleStatusHistoryTable(
                ID=spec.ID,
                Module_ID=spec.Module_ID,
                Status=spec.Status,
                Created_Date=spec.Created_Date,
                Created_By_UUID=spec.Created_By_UUID,
            )
        ]
