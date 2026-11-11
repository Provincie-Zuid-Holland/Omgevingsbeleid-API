import uuid
from collections.abc import Sequence
from datetime import datetime

from app.core.db.base import Base
from app.core.tables.werkingsgebieden import InputGeoWerkingsgebiedenTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BasePersistHandler,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)


class InputGeoWerkingsgebiedenSpec(Spec):
    id: uuid.UUID | None = None
    title: str
    description: str = ""
    created_date: datetime | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "id is not set which is expected to happen at this stage."
        return self.id


class InputGeoWerkingsgebiedenPrefillHandler(BasePrefillHandler[InputGeoWerkingsgebiedenSpec]):
    def fill(
        self, record: Record[InputGeoWerkingsgebiedenSpec], context: PrefillContext
    ) -> Record[InputGeoWerkingsgebiedenSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        return record


class InputGeoWerkingsgebiedenPersistHandler(BasePersistHandler[InputGeoWerkingsgebiedenSpec]):
    def to_rows(self, record: Record[InputGeoWerkingsgebiedenSpec], context: PersistContext) -> Sequence[Base]:
        spec: InputGeoWerkingsgebiedenSpec = record.spec
        return [
            InputGeoWerkingsgebiedenTable(
                id=spec.id,
                created_date=spec.created_date,
                title=spec.title,
                description=spec.description,
            )
        ]
