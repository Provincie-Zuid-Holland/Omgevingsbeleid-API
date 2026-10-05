import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from app.core.db import Base
from app.core.tables.publications import PublicationDocVersionTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationDocVersionSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "doc_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None

    doc_id: Link
    expression_language: str = "nld"
    expression_date: str = "2025-01-01"
    expression_version: int

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationDocVersionPrefillHandler(BasePrefillHandler[PublicationDocVersionSpec]):
    def fill(
        self, record: Record[PublicationDocVersionSpec], context: PrefillContext
    ) -> Record[PublicationDocVersionSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationDocVersionPersistHandler(BasePersistHandler[PublicationDocVersionSpec]):
    def to_rows(self, record: Record[PublicationDocVersionSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationDocVersionSpec = record.spec
        return [
            PublicationDocVersionTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                doc_id=spec.doc_id,
                expression_language=spec.expression_language,
                expression_date=spec.expression_date,
                expression_version=spec.expression_version,
            )
        ]
