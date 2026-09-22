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
    __link_fields__: ClassVar[set[str]] = {"Created_By_UUID", "Modified_By_UUID"}

    id: uuid.UUID | None = None
    Created_Date: datetime | None = None
    Created_By_UUID: Link | None = None
    Modified_Date: datetime | None = None
    Modified_By_UUID: Link | None = None

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
                Created_Date=spec.Created_Date,
                Created_By_UUID=spec.Created_By_UUID,
                Modified_Date=spec.Modified_Date,
                Modified_By_UUID=spec.Modified_By_UUID,
                name=spec.name,
                type=spec.type,
            )
        ]
