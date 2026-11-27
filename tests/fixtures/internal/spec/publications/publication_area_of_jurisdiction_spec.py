import uuid
from collections.abc import Sequence
from datetime import date, datetime
from typing import ClassVar

from app.core.db import Base
from app.core.tables.publications import PublicationAreaOfJurisdictionTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class PublicationAreaOfJurisdictionSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None

    title: str
    administrative_borders_id: str = "PV00"
    administrative_borders_domain: str = "NL.BI.BestuurlijkGebied"
    administrative_borders_date: date

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id


class PublicationAreaOfJurisdictionPrefillHandler(BasePrefillHandler[PublicationAreaOfJurisdictionSpec]):
    def fill(
        self, record: Record[PublicationAreaOfJurisdictionSpec], context: PrefillContext
    ) -> Record[PublicationAreaOfJurisdictionSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class PublicationAreaOfJurisdictionPersistHandler(BasePersistHandler[PublicationAreaOfJurisdictionSpec]):
    def to_rows(self, record: Record[PublicationAreaOfJurisdictionSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationAreaOfJurisdictionSpec = record.spec
        return [
            PublicationAreaOfJurisdictionTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                title=spec.title,
                administrative_borders_id=spec.administrative_borders_id,
                administrative_borders_domain=spec.administrative_borders_domain,
                administrative_borders_date=spec.administrative_borders_date,
            )
        ]
