import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from app.core.db import Base
from app.core.tables.publications import PublicationActVersionTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationActVersionSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "act_id", "consolidation_purpose_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None

    act_id: Link
    consolidation_purpose_id: Link
    expression_language: str = "nld"
    expression_date: str = "2025-01-01"
    expression_version: int

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationActVersionPrefillHandler(BasePrefillHandler[PublicationActVersionSpec]):
    def fill(
        self, record: Record[PublicationActVersionSpec], context: PrefillContext
    ) -> Record[PublicationActVersionSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationActVersionPersistHandler(BasePersistHandler[PublicationActVersionSpec]):
    def to_rows(self, record: Record[PublicationActVersionSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationActVersionSpec = record.spec
        return [
            PublicationActVersionTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                act_id=spec.act_id,
                consolidation_purpose_id=spec.consolidation_purpose_id,
                expression_language=spec.expression_language,
                expression_date=spec.expression_date,
                expression_version=spec.expression_version,
            )
        ]
