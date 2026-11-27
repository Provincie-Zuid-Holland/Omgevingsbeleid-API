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
        "module_manager_1_id",
        "module_manager_2_id",
    }

    module_id: int

    # Sensible defaults for most cases
    activated: bool = True
    closed: bool = False
    successful: bool = False
    temporary_locked: bool = False

    title: str
    description: str
    module_manager_1_id: Link | None = None
    module_manager_2_id: Link | None = None

    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        return self.module_id


class ModulePrefillHandler(BasePrefillHandler[ModuleSpec]):
    def fill(self, record: Record[ModuleSpec], context: PrefillContext) -> Record[ModuleSpec]:
        record = super().fill(record, context)

        return record


class ModulePersistHandler(BasePersistHandler[ModuleSpec]):
    def to_rows(self, record: Record[ModuleSpec], context: PersistContext) -> Sequence[Base]:
        spec: ModuleSpec = record.spec
        return [
            ModuleTable(
                module_id=spec.module_id,
                activated=spec.activated,
                closed=spec.closed,
                successful=spec.successful,
                temporary_locked=spec.temporary_locked,
                title=spec.title,
                description=spec.description,
                module_manager_1_id=spec.module_manager_1_id,
                module_manager_2_id=spec.module_manager_2_id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                modified_date=spec.modified_date,
                modified_by_id=spec.modified_by_id,
            ),
        ]
