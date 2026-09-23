import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from app.core.db.base import Base
from app.core.tables.others import ObjectRelatedFileTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Ref,
    Spec,
)


class ObjectRelatedFileSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "File_Ref"}

    UUID: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None

    Code: str
    File_Ref: Ref
    Title: str

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.UUID, "UUID is not set which is expected to happen at this stage."
        return self.UUID


class ObjectRelatedFilePrefillHandler(BasePrefillHandler[ObjectRelatedFileSpec]):
    def fill(self, record: Record[ObjectRelatedFileSpec], context: PrefillContext) -> Record[ObjectRelatedFileSpec]:
        record = super().fill(record, context)

        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid4()

        return record


class ObjectRelatedFilePersistHandler(BasePersistHandler[ObjectRelatedFileSpec]):
    def to_rows(self, record: Record[ObjectRelatedFileSpec], context: PersistContext) -> Sequence[Base]:
        spec: ObjectRelatedFileSpec = record.spec
        return [
            ObjectRelatedFileTable(
                UUID=spec.UUID,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                Code=spec.Code,
                File_UUID=spec.File_Ref,
                Title=spec.Title,
            )
        ]
