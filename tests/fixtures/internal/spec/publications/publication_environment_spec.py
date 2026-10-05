import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from app.core.db import Base
from app.core.tables.publications import PublicationEnvironmentTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationEnvironmentSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "modified_by_id", "active_state_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    modified_date: datetime | None = None
    modified_by_id: Link | None = None

    title: str
    code: str = "PROD"  # Used to map secret data to the environment like API Keys
    description: str

    province_id: str = "pv00"
    authority_id: str = "00000000000000000000"
    submitter_id: str = "00000000000000000000"
    governing_body_type: str = "provinciale_staten"
    frbr_country: str = "nl"
    frbr_language: str = "nld"

    is_active: bool = True
    has_state: bool = False
    can_validate: bool = True
    can_publicate: bool = True
    is_locked: bool = False
    active_state_id: Link | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationEnvironmentPrefillHandler(BasePrefillHandler[PublicationEnvironmentSpec]):
    def fill(
        self, record: Record[PublicationEnvironmentSpec], context: PrefillContext
    ) -> Record[PublicationEnvironmentSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationEnvironmentPersistHandler(BasePersistHandler[PublicationEnvironmentSpec]):
    def to_rows(self, record: Record[PublicationEnvironmentSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationEnvironmentSpec = record.spec
        return [
            PublicationEnvironmentTable(
                id=spec.id,
                created_date=spec.created_date,
                modified_date=spec.modified_date,
                created_by_id=spec.created_by_id,
                modified_by_id=spec.modified_by_id,
                title=spec.title,
                code=spec.code,
                description=spec.description,
                province_id=spec.province_id,
                authority_id=spec.authority_id,
                submitter_id=spec.submitter_id,
                governing_body_type=spec.governing_body_type,
                frbr_country=spec.frbr_country,
                frbr_language=spec.frbr_language,
                is_active=spec.is_active,
                has_state=spec.has_state,
                can_validate=spec.can_validate,
                can_publicate=spec.can_publicate,
                is_locked=spec.is_locked,
                active_state_id=spec.active_state_id,
            )
        ]
