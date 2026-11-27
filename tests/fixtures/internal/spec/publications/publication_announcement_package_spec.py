import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar, Literal

from app.core.db import Base
from app.core.tables.publications import PublicationAnnouncementPackageTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationAnnouncementPackageSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {
        "created_by_id",
        "modified_by_id",
        "announcement_id",
        "doc_version_id",
        "zip_id",
        "used_environment_state_id",
        "created_environment_state_id",
    }

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    announcement_id: Link
    doc_version_id: Link | None = None
    zip_id: Link

    package_type: Literal["validation", "publication"] = "validation"
    report_status: Literal["not_applicable", "pending", "valid", "failed", "aborted"] = "not_applicable"

    delivery_id: str | None = None

    used_environment_state_id: Link | None = None
    created_environment_state_id: Link | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationAnnouncementPackagePrefillHandler(BasePrefillHandler[PublicationAnnouncementPackageSpec]):
    def fill(
        self, record: Record[PublicationAnnouncementPackageSpec], context: PrefillContext
    ) -> Record[PublicationAnnouncementPackageSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()
        if record.spec.delivery_id is None:
            record.spec.delivery_id = str(uuid.uuid4())

        return record


class PublicationAnnouncementPackagePersistHandler(BasePersistHandler[PublicationAnnouncementPackageSpec]):
    def to_rows(self, record: Record[PublicationAnnouncementPackageSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationAnnouncementPackageSpec = record.spec
        return [
            PublicationAnnouncementPackageTable(
                id=spec.id,
                created_date=spec.created_date,
                modified_date=spec.modified_date,
                created_by_id=spec.created_by_id,
                modified_by_id=spec.modified_by_id,
                announcement_id=spec.announcement_id,
                doc_version_id=spec.doc_version_id,
                zip_id=spec.zip_id,
                package_type=spec.package_type,
                report_status=spec.report_status,
                delivery_id=spec.delivery_id,
                used_environment_state_id=spec.used_environment_state_id,
                created_environment_state_id=spec.created_environment_state_id,
            )
        ]
