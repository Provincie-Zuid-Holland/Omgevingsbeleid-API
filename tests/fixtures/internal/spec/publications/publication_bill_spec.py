import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar, Literal

from app.core.db import Base
from app.core.tables.publications import PublicationBillTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationBillSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "modified_by_id", "environment_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    environment_id: Link
    document_type: Literal["omgevingsvisie", "programma"] = "omgevingsvisie"

    work_province_id: str = "pv00"
    work_country: str = "nl"
    work_date: str = "2025"
    work_other: str

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationBillPrefillHandler(BasePrefillHandler[PublicationBillSpec]):
    def fill(self, record: Record[PublicationBillSpec], context: PrefillContext) -> Record[PublicationBillSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationBillPersistHandler(BasePersistHandler[PublicationBillSpec]):
    def to_rows(self, record: Record[PublicationBillSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationBillSpec = record.spec
        return [
            PublicationBillTable(
                id=spec.id,
                created_date=spec.created_date,
                modified_date=spec.modified_date,
                created_by_id=spec.created_by_id,
                modified_by_id=spec.modified_by_id,
                environment_id=spec.environment_id,
                document_type=spec.document_type,
                work_province_id=spec.work_province_id,
                work_country=spec.work_country,
                work_date=spec.work_date,
                work_other=spec.work_other,
            )
        ]
