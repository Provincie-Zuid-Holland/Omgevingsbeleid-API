import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from app.core.db import Base
from app.core.tables.others import HoofdlijnTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class HoofdlijnSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "modified_by_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    name: str
    type: str

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "UUID is not set which is expected to happen at this stage."
        return self.id


class HoofdlijnPrefillHandler(BasePrefillHandler[HoofdlijnSpec]):
    def fill(self, record: Record[HoofdlijnSpec], context: PrefillContext) -> Record[HoofdlijnSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class HoofdlijnPersistHandler(BasePersistHandler[HoofdlijnSpec]):
    def to_rows(self, record: Record[HoofdlijnSpec], context: PersistContext) -> Sequence[Base]:
        spec: HoofdlijnSpec = record.spec
        return [
            HoofdlijnTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                modified_date=spec.modified_date,
                modified_by_id=spec.modified_by_id,
                name=spec.name,
                type=spec.type,
            )
        ]
