import hashlib
from typing import ClassVar, List, Optional, Sequence, Set, Tuple
import uuid

from shapely.geometry import Polygon
from app.core.db.base import Base
from shapely import wkb
from app.core.tables.werkingsgebieden import (
    InputGeoOnderverdelingenTable,
    InputGeoWerkingsgebiedOnderverdelingTable,
)
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    Spec,
    Record,
    PrimaryKey,
    PersistContext,
    BasePersistHandler,
)

from datetime import datetime


from tests.fixtures.internal.types import (
    Link,
)


class InputGeoOnderverdelingSpec(Spec):
    __link_fields__: ClassVar[Set[str]] = {"Owners"}

    UUID: Optional[uuid.UUID] = None
    Title: str
    Description: str = ""
    Created_Date: Optional[datetime] = None
    Symbol: Optional[str] = None
    Points: List[Tuple[int, int]]
    Owners: List[Link]

    Geometry: Optional[bytes] = None
    Geometry_Hash: str = ""
    GML: str = ""

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.UUID, "UUID is not set which is expected to happen at this stage."
        return self.UUID


class InputGeoOnderverdelingPrefillHandler(BasePrefillHandler[InputGeoOnderverdelingSpec]):
    def fill(
        self, record: Record[InputGeoOnderverdelingSpec], context: PrefillContext
    ) -> Record[InputGeoOnderverdelingSpec]:
        record = super().fill(record, context)

        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid4()

        polygon = Polygon(record.spec.Points)
        gml: str = self._polygon_gml(polygon, f"gml-id-{context.spec_count}")
        binary: bytes = wkb.dumps(polygon)
        checksum: str = hashlib.sha512(binary).hexdigest()

        record.spec.Geometry = binary
        record.spec.Geometry_Hash = checksum
        record.spec.GML = gml
        record.spec.Symbol = record.spec.Symbol or "ES225"

        return record

    def _polygon_gml(self, polygon: Polygon, gml_id: str) -> str:
        pos_list = " ".join(f"{str(int(x))} {str(int(y))}" for x, y in polygon.exterior.coords)
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

        records: List[Base] = [
            InputGeoOnderverdelingenTable(
                UUID=spec.UUID,
                Created_Date=spec.Created_Date,
                Title=spec.Title,
                Description=spec.Description,
                Symbol=spec.Symbol,
                Geometry=spec.Geometry,
                Geometry_Hash=spec.Geometry_Hash,
                GML=spec.GML,
            )
        ]
        for owner_uuid in spec.Owners:
            records.append(
                InputGeoWerkingsgebiedOnderverdelingTable(
                    Werkingsgebied_UUID=owner_uuid,
                    Onderverdeling_UUID=spec.UUID,
                )
            )

        return records
