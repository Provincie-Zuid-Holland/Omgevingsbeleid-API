import hashlib
import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import ClassVar

from shapely import wkb
from shapely.geometry import Polygon

from app.core.db.base import Base
from app.core.tables.werkingsgebieden import (
    InputGeoOnderverdelingenTable,
    InputGeoWerkingsgebiedOnderverdelingTable,
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


class InputGeoOnderverdelingSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"owners"}

    id: uuid.UUID | None = None
    title: str
    description: str = ""
    created_date: datetime | None = None
    symbol: str | None = None
    points: list[tuple[int, int]]
    owners: list[Link]

    geometry: bytes | None = None
    geometry_hash: str = ""
    gml: str = ""

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "id is not set which is expected to happen at this stage."
        return self.id


class InputGeoOnderverdelingPrefillHandler(BasePrefillHandler[InputGeoOnderverdelingSpec]):
    def fill(
        self, record: Record[InputGeoOnderverdelingSpec], context: PrefillContext
    ) -> Record[InputGeoOnderverdelingSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        polygon = Polygon(record.spec.points)
        gml: str = self._polygon_gml(polygon, f"gml-id-{context.spec_count}")
        binary: bytes = wkb.dumps(polygon)
        checksum: str = hashlib.sha512(binary).hexdigest()

        record.spec.geometry = binary
        record.spec.geometry_hash = checksum
        record.spec.gml = gml
        record.spec.symbol = record.spec.symbol or "ES225"

        return record

    def _polygon_gml(self, polygon: Polygon, gml_id: str) -> str:
        pos_list = " ".join(f"{int(x)!s} {int(y)!s}" for x, y in polygon.exterior.coords)
        return (
            f'<gml:Polygon xmlns:gml="http://www.opengis.net/gml/3.2" srsName="urn:ogc:def:crs:EPSG::28992" '
            f'srsDimension="2" gml:id="{gml_id}">'
            f"<gml:exterior><gml:LinearRing>"
            f"<gml:posList>{pos_list}</gml:posList>"
            f"</gml:LinearRing></gml:exterior>"
            f"</gml:Polygon>"
        )


class InputGeoOnderverdelingPersistHandler(BasePersistHandler[InputGeoOnderverdelingSpec]):
    def to_rows(self, record: Record[InputGeoOnderverdelingSpec], context: PersistContext) -> Sequence[Base]:
        spec: InputGeoOnderverdelingSpec = record.spec

        records: list[Base] = [
            InputGeoOnderverdelingenTable(
                id=spec.id,
                created_date=spec.created_date,
                title=spec.title,
                description=spec.description,
                symbol=spec.symbol,
                geometry=spec.geometry,
                geometry_hash=spec.geometry_hash[:64],
                gml=spec.gml,
            )
        ]
        for owner_uuid in spec.owners:
            records.append(
                InputGeoWerkingsgebiedOnderverdelingTable(
                    werkingsgebied_id=owner_uuid,
                    onderverdeling_id=spec.id,
                )
            )

        return records
