from datetime import datetime
from typing import ClassVar, Optional, Sequence, Set


from app.core.db.base import Base
from app.core.tables.modules import ModuleStatusHistoryTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import Spec, Record, PrimaryKey, PersistContext, BasePersistHandler, Link


class ModuleStatusHistorySpec(Spec):
    __link_fields__: ClassVar[Set[str]] = {"Created_By_UUID"}

    ID: Optional[int] = None
    Module_ID: Optional[int] = None
    Status: Optional[str] = None

    Created_Date: Optional[datetime] = None
    Created_By_UUID: Optional[Link] = None

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
