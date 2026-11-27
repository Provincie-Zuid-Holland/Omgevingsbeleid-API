import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from app.core.db import Base
from app.core.tables.publications import PublicationBillVersionTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationBillVersionSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "bill_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None

    bill_id: Link
    expression_language: str = "nld"
    expression_date: str = "2025-01-01"
    expression_version: int

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationBillVersionPrefillHandler(BasePrefillHandler[PublicationBillVersionSpec]):
    def fill(
        self, record: Record[PublicationBillVersionSpec], context: PrefillContext
    ) -> Record[PublicationBillVersionSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationBillVersionPersistHandler(BasePersistHandler[PublicationBillVersionSpec]):
    def to_rows(self, record: Record[PublicationBillVersionSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationBillVersionSpec = record.spec
        return [
            PublicationBillVersionTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                bill_id=spec.bill_id,
                expression_language=spec.expression_language,
                expression_date=spec.expression_date,
                expression_version=spec.expression_version,
            )
        ]
