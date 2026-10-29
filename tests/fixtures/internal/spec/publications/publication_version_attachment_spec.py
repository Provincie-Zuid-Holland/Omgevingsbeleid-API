from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar, cast

from app.core.db import Base
from app.core.tables.publications import PublicationVersionAttachmentTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.spec.publications.publication_storage_file_spec import PublicationStorageFileSpec
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Ref,
    Spec,
)


class PublicationVersionAttachmentSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "modified_by_id", "publication_version_id", "file_id"}

    id: int | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    publication_version_id: Link
    file_id: Link
    title: str

    # Will be copied from the file if you leave it empty and set file_id to a Ref
    filename: str = ""

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationVersionAttachmentPrefillHandler(BasePrefillHandler[PublicationVersionAttachmentSpec]):
    def fill(
        self, record: Record[PublicationVersionAttachmentSpec], context: PrefillContext
    ) -> Record[PublicationVersionAttachmentSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = context.spec_count

        if not record.spec.filename:
            file_ref: Link = record.spec.file_id
            assert isinstance(file_ref, Ref) and file_ref.spec_type == PublicationStorageFileSpec, (
                "Set `filename` or point `file_id` to a PublicationStorageFileSpec Ref."
            )
            file: Record[PublicationStorageFileSpec] = cast(Record[PublicationStorageFileSpec], context.find(file_ref))
            record.spec.filename = file.spec.filename

        return record


class PublicationVersionAttachmentPersistHandler(BasePersistHandler[PublicationVersionAttachmentSpec]):
    def to_rows(self, record: Record[PublicationVersionAttachmentSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationVersionAttachmentSpec = record.spec
        return [
            PublicationVersionAttachmentTable(
                id=spec.id,
                created_date=spec.created_date,
                modified_date=spec.modified_date,
                created_by_id=spec.created_by_id,
                modified_by_id=spec.modified_by_id,
                publication_version_id=spec.publication_version_id,
                file_id=spec.file_id,
                filename=spec.filename,
                title=spec.title,
            )
        ]
