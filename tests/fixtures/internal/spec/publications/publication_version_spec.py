import uuid
from collections.abc import Sequence
from datetime import date, datetime
from typing import ClassVar, Literal

from pydantic import Field

from app.core.db import Base
from app.core.tables.publications import PublicationVersionTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationVersionSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "modified_by_id", "publication_id", "module_status_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    publication_id: Link
    module_status_id: Link

    bill_metadata: dict = Field(default_factory=dict)
    bill_compact: dict = Field(default_factory=dict)
    procedural: dict = Field(default_factory=dict)

    effective_date: date | None = None
    announcement_date: date | None = None

    is_locked: bool = False
    deleted_at: datetime | None = None

    status: Literal[
        "not_applicable",
        "active",
        "validation",
        "validation_failed",
        "publication",
        "publication_failed",
        "publication_aborted",
        "announcement",
        "completed",
    ] = "not_applicable"
    mutation_strategy: Literal["renvooi", "replace"] = "renvooi"

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationVersionPrefillHandler(BasePrefillHandler[PublicationVersionSpec]):
    def fill(self, record: Record[PublicationVersionSpec], context: PrefillContext) -> Record[PublicationVersionSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationVersionPersistHandler(BasePersistHandler[PublicationVersionSpec]):
    def to_rows(self, record: Record[PublicationVersionSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationVersionSpec = record.spec
        return [
            PublicationVersionTable(
                id=spec.id,
                created_date=spec.created_date,
                modified_date=spec.modified_date,
                created_by_id=spec.created_by_id,
                modified_by_id=spec.modified_by_id,
                publication_id=spec.publication_id,
                module_status_id=spec.module_status_id,
                bill_metadata=spec.bill_metadata,
                bill_compact=spec.bill_compact,
                procedural=spec.procedural,
                effective_date=spec.effective_date,
                announcement_date=spec.announcement_date,
                is_locked=spec.is_locked,
                deleted_at=spec.deleted_at,
                status=spec.status,
                mutation_strategy=spec.mutation_strategy,
            )
        ]
