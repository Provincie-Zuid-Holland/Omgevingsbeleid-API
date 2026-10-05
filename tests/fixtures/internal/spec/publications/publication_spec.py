import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar, Literal

from app.core.db import Base
from app.core.tables.publications import PublicationTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {
        "created_by_id",
        "modified_by_id",
        "module_id",
        "template_id",
        "environment_id",
        "act_id",
    }

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    module_id: Link
    document_type: Literal["omgevingsvisie", "programma"] = "omgevingsvisie"
    procedure_type: Literal["draft", "final"] = "final"
    template_id: Link
    environment_id: Link
    act_id: Link

    is_locked: bool = False

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationPrefillHandler(BasePrefillHandler[PublicationSpec]):
    def fill(self, record: Record[PublicationSpec], context: PrefillContext) -> Record[PublicationSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationPersistHandler(BasePersistHandler[PublicationSpec]):
    def to_rows(self, record: Record[PublicationSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationSpec = record.spec
        return [
            PublicationTable(
                id=spec.id,
                created_date=spec.created_date,
                modified_date=spec.modified_date,
                created_by_id=spec.created_by_id,
                modified_by_id=spec.modified_by_id,
                module_id=spec.module_id,
                document_type=spec.document_type,
                procedure_type=spec.procedure_type,
                template_id=spec.template_id,
                environment_id=spec.environment_id,
                act_id=spec.act_id,
                is_locked=spec.is_locked,
            )
        ]
