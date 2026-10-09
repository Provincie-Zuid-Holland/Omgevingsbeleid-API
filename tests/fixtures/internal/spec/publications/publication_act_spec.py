from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar, Literal
from uuid import UUID, uuid4

from pydantic import Field

from app.core.db import Base
from app.core.tables.publications import PublicationActTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationActSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {
        "created_by_id",
        "modified_by_id",
        "environment_id",
        "withdrawal_purpose_id",
    }

    id: int | None = None
    uuid: UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    environment_id: Link
    document_type: Literal["omgevingsvisie", "programma"] = "omgevingsvisie"

    title: str
    is_active: bool = True

    meta_data: dict = Field(default_factory=dict)
    meta_data_is_locked: bool = False

    work_province_id: str = "pv00"
    work_country: str = "nl"
    work_date: str = "2025"
    work_other: str

    withdrawal_purpose_id: Link | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationActPrefillHandler(BasePrefillHandler[PublicationActSpec]):
    def fill(self, record: Record[PublicationActSpec], context: PrefillContext) -> Record[PublicationActSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = context.spec_count
        if record.spec.uuid is None:
            record.spec.uuid = uuid4()

        return record


class PublicationActPersistHandler(BasePersistHandler[PublicationActSpec]):
    def to_rows(self, record: Record[PublicationActSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationActSpec = record.spec
        return [
            PublicationActTable(
                id=spec.id,
                uuid=spec.uuid,
                created_date=spec.created_date,
                modified_date=spec.modified_date,
                created_by_id=spec.created_by_id,
                modified_by_id=spec.modified_by_id,
                environment_id=spec.environment_id,
                document_type=spec.document_type,
                procedure_type=None,
                title=spec.title,
                is_active=spec.is_active,
                meta_data=spec.meta_data,
                meta_data_is_locked=spec.meta_data_is_locked,
                work_province_id=spec.work_province_id,
                work_country=spec.work_country,
                work_date=spec.work_date,
                work_other=spec.work_other,
                withdrawal_purpose_id=spec.withdrawal_purpose_id,
            )
        ]
