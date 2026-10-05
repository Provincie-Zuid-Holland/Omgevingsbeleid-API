import uuid
from collections.abc import Sequence
from datetime import date, datetime
from typing import ClassVar

from pydantic import Field

from app.core.db import Base
from app.core.tables.publications import PublicationAnnouncementTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationAnnouncementSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "modified_by_id", "act_package_id", "publication_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    act_package_id: Link
    publication_id: Link

    meta_data: dict = Field(default_factory=dict)
    procedural: dict = Field(default_factory=dict)
    content: dict = Field(default_factory=dict)

    announcement_date: date | None = None
    is_locked: bool = False

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationAnnouncementPrefillHandler(BasePrefillHandler[PublicationAnnouncementSpec]):
    def fill(
        self, record: Record[PublicationAnnouncementSpec], context: PrefillContext
    ) -> Record[PublicationAnnouncementSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationAnnouncementPersistHandler(BasePersistHandler[PublicationAnnouncementSpec]):
    def to_rows(self, record: Record[PublicationAnnouncementSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationAnnouncementSpec = record.spec
        return [
            PublicationAnnouncementTable(
                id=spec.id,
                created_date=spec.created_date,
                modified_date=spec.modified_date,
                created_by_id=spec.created_by_id,
                modified_by_id=spec.modified_by_id,
                act_package_id=spec.act_package_id,
                publication_id=spec.publication_id,
                meta_data=spec.meta_data,
                procedural=spec.procedural,
                content=spec.content,
                announcement_date=spec.announcement_date,
                is_locked=spec.is_locked,
            )
        ]
