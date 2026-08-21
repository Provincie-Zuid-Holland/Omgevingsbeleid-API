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
    __link_fields__: ClassVar[set[str]] = {"Created_By_UUID"}

    UUID: uuid.UUID | None = None
    Created_Date: datetime | None = None
    Created_By_UUID: Link | None = None

    Name: str
    Type: str

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.UUID, "UUID is not set which is expected to happen at this stage."
        return self.UUID


class HoofdlijnPrefillHandler(BasePrefillHandler[HoofdlijnSpec]):
    def fill(self, record: Record[HoofdlijnSpec], context: PrefillContext) -> Record[HoofdlijnSpec]:
        record = super().fill(record, context)

        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid4()

        return record


class HoofdlijnPersistHandler(BasePersistHandler[HoofdlijnSpec]):
    def to_rows(self, record: Record[HoofdlijnSpec], context: PersistContext) -> Sequence[Base]:
        spec: HoofdlijnSpec = record.spec
        return [
            HoofdlijnTable(
                UUID=spec.UUID,
                Created_Date=spec.Created_Date,
                Created_By_UUID=spec.Created_By_UUID,
                Name=spec.Name,
                Type=spec.Type,
            )
        ]
