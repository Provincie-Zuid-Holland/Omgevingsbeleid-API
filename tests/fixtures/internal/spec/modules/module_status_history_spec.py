from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from app.core.db.base import Base
from app.core.tables.modules import ModuleStatusHistoryTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import BasePersistHandler, Link, PersistContext, PrimaryKey, Record, Spec


class ModuleStatusHistorySpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id"}

    id: int | None = None
    module_id: int | None = None
    Status: str | None = None

    created_date: datetime | None = None
    created_by_id: Link | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "ID is not set which is expected to happen at this stage."
        return self.id


class ModuleStatusHistoryPrefillHandler(BasePrefillHandler[ModuleStatusHistorySpec]):
    def fill(self, record: Record[ModuleStatusHistorySpec], context: PrefillContext) -> Record[ModuleStatusHistorySpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = context.spec_count

        return record


class ModuleStatusHistoryPersistHandler(BasePersistHandler[ModuleStatusHistorySpec]):
    def to_rows(self, record: Record[ModuleStatusHistorySpec], context: PersistContext) -> Sequence[Base]:
        spec: ModuleStatusHistorySpec = record.spec
        return [
            ModuleStatusHistoryTable(
                id=spec.id,
                module_id=spec.module_id,
                status=spec.Status,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
            )
        ]
