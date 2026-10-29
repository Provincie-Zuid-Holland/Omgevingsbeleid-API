import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from pydantic import Field

from app.core.db import Base
from app.core.tables.publications import (
    PublicationEnvironmentStateTable,
)
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationEnvironmentStateSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "environment_id", "adjust_on_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None

    environment_id: Link
    adjust_on_id: Link | None
    state: dict = Field(default_factory=dict)
    is_activated: bool = False
    activated_datetime: datetime | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationEnvironmentStatePrefillHandler(BasePrefillHandler[PublicationEnvironmentStateSpec]):
    def fill(
        self, record: Record[PublicationEnvironmentStateSpec], context: PrefillContext
    ) -> Record[PublicationEnvironmentStateSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationEnvironmentStatePersistHandler(BasePersistHandler[PublicationEnvironmentStateSpec]):
    def to_rows(self, record: Record[PublicationEnvironmentStateSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationEnvironmentStateSpec = record.spec
        return [
            PublicationEnvironmentStateTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                environment_id=spec.environment_id,
                adjust_on_id=spec.adjust_on_id,
                state=spec.state,
                is_activated=spec.is_activated,
                activated_datetime=spec.activated_datetime,
            )
        ]
