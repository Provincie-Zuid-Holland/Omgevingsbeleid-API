from typing import Optional, Sequence
import uuid


from app.core.db.base import Base
from app.core.tables.others import ObjectRelatedFileTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    Spec,
    Record,
    PrimaryKey,
    PersistContext,
    BasePersistHandler,
    Ref,
)

from datetime import datetime
from typing import ClassVar, Set


from tests.fixtures.internal.types import (
    Link,
)


class ObjectRelatedFileSpec(Spec):
    __link_fields__: ClassVar[Set[str]] = {"Created_By_UUID", "File_Ref"}

    UUID: Optional[uuid.UUID] = None
    Created_Date: Optional[datetime] = None
    Created_By_UUID: Optional[Link] = None

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
                Created_Date=spec.Created_Date,
                Created_By_UUID=spec.Created_By_UUID,
                Code=spec.Code,
                File_UUID=spec.File_Ref,
                Title=spec.Title,
            )
        ]
