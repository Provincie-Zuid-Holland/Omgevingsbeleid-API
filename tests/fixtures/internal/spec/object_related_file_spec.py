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
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "file_ref"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None

    code: str
    file_ref: Ref
    title: str

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "UUID is not set which is expected to happen at this stage."
        return self.id


class ObjectRelatedFilePrefillHandler(BasePrefillHandler[ObjectRelatedFileSpec]):
    def fill(self, record: Record[ObjectRelatedFileSpec], context: PrefillContext) -> Record[ObjectRelatedFileSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class ObjectRelatedFilePersistHandler(BasePersistHandler[ObjectRelatedFileSpec]):
    def to_rows(self, record: Record[ObjectRelatedFileSpec], context: PersistContext) -> Sequence[Base]:
        spec: ObjectRelatedFileSpec = record.spec
        return [
            ObjectRelatedFileTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                code=spec.code,
                file_id=spec.file_ref,
                title=spec.title,
            )
        ]
