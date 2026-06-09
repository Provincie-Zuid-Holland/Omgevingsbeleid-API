from typing import Optional, Sequence, cast
import uuid

from pydantic import Field


from app.core.db.base import Base
from app.core.tables.others import AreasTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    Spec,
    Record,
    PrimaryKey,
    PersistContext,
    BasePersistHandler,
    DATETIME_T0,
    Ref,
)
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec

from datetime import datetime
from typing import ClassVar, Set


from tests.fixtures.internal.types import (
    Link,
)


class AreaSpec(Spec):
    __link_fields__: ClassVar[Set[str]] = {"Created_By_UUID"}

    UUID: Optional[uuid.UUID] = None
    Created_Date: Optional[datetime] = None
    Created_By_UUID: Optional[Link] = None

    Source_Ref: Ref

    # These will be filled if you just set Source_Ref
    Source_UUID: Optional[uuid.UUID] = None
    Shape: Optional[bytes] = None
    Gml: str = ""
    Source_Title: str = ""
    Source_Symbol: Optional[str] = None
    Source_Created_Date: datetime = Field(default=DATETIME_T0)
    Source_Geometry_Index: Optional[str] = None
    Source_Geometry_Hash: Optional[str] = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.UUID, "UUID is not set which is expected to happen at this stage."
        return self.UUID


class AreaPrefillHandler(BasePrefillHandler[AreaSpec]):
    def fill(self, record: Record[AreaSpec], context: PrefillContext) -> Record[AreaSpec]:
        record = super().fill(record, context)

        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid4()

        assert record.spec.Source_Ref.spec_type == InputGeoOnderverdelingSpec
        source_generic: Record[Spec] = context.find(record.spec.Source_Ref)
        source: Record[InputGeoOnderverdelingSpec] = cast(Record[InputGeoOnderverdelingSpec], source_generic)

        record.spec.Source_UUID = source.spec.UUID
        record.spec.Shape = source.spec.Geometry
        record.spec.Gml = source.spec.GML
        record.spec.Source_Title = source.spec.Title
        record.spec.Source_Symbol = source.spec.Symbol
        record.spec.Source_Created_Date = source.spec.Created_Date
        record.spec.Source_Geometry_Index = source.spec.Geometry_Hash[:10]
        record.spec.Source_Geometry_Hash = source.spec.Geometry_Hash

        return record


class AreaPersistHandler(BasePersistHandler[AreaSpec]):
    def to_rows(self, record: Record[AreaSpec], context: PersistContext) -> Sequence[Base]:
        spec: AreaSpec = record.spec
        return [
            AreasTable(
                UUID=spec.UUID,
                Created_Date=spec.Created_Date,
                Created_By_UUID=spec.Created_By_UUID,
                Shape=spec.Shape,
                Gml=spec.Gml,
                Source_UUID=spec.Source_UUID,
                Source_Title=spec.Source_Title,
                Source_Symbol=spec.Source_Symbol,
                Source_Created_Date=spec.Source_Created_Date,
                Source_Geometry_Index=spec.Source_Geometry_Index,
                Source_Geometry_Hash=spec.Source_Geometry_Hash,
            )
        ]
