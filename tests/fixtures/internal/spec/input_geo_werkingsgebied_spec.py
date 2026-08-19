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
    UUID: uuid.UUID | None = None
    Title: str
    Description: str = ""
    Created_Date: datetime | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.UUID, "UUID is not set which is expected to happen at this stage."
        return self.UUID


class InputGeoWerkingsgebiedenPrefillHandler(BasePrefillHandler[InputGeoWerkingsgebiedenSpec]):
    def fill(
        self, record: Record[InputGeoWerkingsgebiedenSpec], context: PrefillContext
    ) -> Record[InputGeoWerkingsgebiedenSpec]:
        record = super().fill(record, context)

        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid4()

        return record


class InputGeoWerkingsgebiedenPersistHandler(BasePersistHandler[InputGeoWerkingsgebiedenSpec]):
    def to_rows(self, record: Record[InputGeoWerkingsgebiedenSpec], context: PersistContext) -> Sequence[Base]:
        spec: InputGeoWerkingsgebiedenSpec = record.spec
        return [
            InputGeoWerkingsgebiedenTable(
                UUID=spec.UUID,
                Created_Date=spec.Created_Date,
                Title=spec.Title,
                Description=spec.Description,
            )
        ]
