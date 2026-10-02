import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar, cast

from pydantic import Field

from app.core.db.base import Base
from app.core.tables.others import AreasTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec
from tests.fixtures.internal.types import (
    DATETIME_T0,
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Ref,
    Spec,
)


class AreaSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None

    source_ref: Ref

    # These will be filled if you just set Source_Ref
    source_id: uuid.UUID | None = None
    shape: bytes | None = None
    gml: str = ""
    source_title: str = ""
    source_symbol: str | None = None
    source_created_date: datetime = Field(default=DATETIME_T0)
    source_geometry_index: str | None = None
    source_geometry_hash: str | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "UUID is not set which is expected to happen at this stage."
        return self.id


class AreaPrefillHandler(BasePrefillHandler[AreaSpec]):
    def fill(self, record: Record[AreaSpec], context: PrefillContext) -> Record[AreaSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        assert record.spec.source_ref.spec_type == InputGeoOnderverdelingSpec
        source_generic: Record[Spec] = context.find(record.spec.source_ref)
        source: Record[InputGeoOnderverdelingSpec] = cast(Record[InputGeoOnderverdelingSpec], source_generic)

        record.spec.source_id = source.spec.UUID
        record.spec.shape = source.spec.Geometry
        record.spec.gml = source.spec.GML
        record.spec.source_title = source.spec.Title
        record.spec.source_symbol = source.spec.Symbol
        record.spec.source_created_date = source.spec.Created_Date
        record.spec.source_geometry_index = source.spec.Geometry_Hash[:10]
        record.spec.source_geometry_hash = source.spec.Geometry_Hash[:64]

        return record


class AreaPersistHandler(BasePersistHandler[AreaSpec]):
    def to_rows(self, record: Record[AreaSpec], context: PersistContext) -> Sequence[Base]:
        spec: AreaSpec = record.spec
        return [
            AreasTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                shape=spec.shape,
                gml=spec.gml,
                source_uuid=spec.source_id,
                source_title=spec.source_title,
                source_symbol=spec.source_symbol,
                source_created_date=spec.source_created_date,
                source_geometry_index=spec.source_geometry_index,
                source_geometry_hash=spec.source_geometry_hash,
            )
        ]
