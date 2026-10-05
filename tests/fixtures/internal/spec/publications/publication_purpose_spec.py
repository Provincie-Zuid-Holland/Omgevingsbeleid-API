import uuid
from collections.abc import Sequence
from datetime import date, datetime
from typing import ClassVar

from app.core.db import Base
from app.core.tables.publications import PublicationPurposeTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationPurposeSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "environment_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None

    environment_id: Link
    purpose_type: str = "consolidation"
    effective_date: date | None = None
    work_province_id: str = "pv00"
    work_date: str = "2025"
    work_other: str

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationPurposePrefillHandler(BasePrefillHandler[PublicationPurposeSpec]):
    def fill(self, record: Record[PublicationPurposeSpec], context: PrefillContext) -> Record[PublicationPurposeSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationPurposePersistHandler(BasePersistHandler[PublicationPurposeSpec]):
    def to_rows(self, record: Record[PublicationPurposeSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationPurposeSpec = record.spec
        return [
            PublicationPurposeTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                environment_id=spec.environment_id,
                purpose_type=spec.purpose_type,
                effective_date=spec.effective_date,
                work_province_id=spec.work_province_id,
                work_date=spec.work_date,
                work_other=spec.work_other,
            )
        ]
