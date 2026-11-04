from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import InputGeoWerkingsgebiedenSpec


def load(col: Collector) -> None:
    # Updated the Input Geo in februari
    with col.with_defaults(
        created_date=datetime(2025, 2, 1, tzinfo=UTC),
        Description="Herziening 2025 - Ontwerp GS",
    ):
        col.adds(
            [
                # Nature - did not change
                InputGeoWerkingsgebiedenSpec(
                    key="nature_v2",
                    title="Nature",
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_west_v2",
                    title="Nature West",
                    points=[(100, 100), (110, 100), (110, 110)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v2")],
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_east_v2",
                    title="Nature east",
                    points=[(110, 110), (120, 110), (120, 120)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v2")],
                ),
                # Water - Only the sea moved a bit
                InputGeoWerkingsgebiedenSpec(
                    key="water_v2",
                    title="Water",
                ),
                InputGeoOnderverdelingSpec(
                    key="sea_v2",
                    title="sea",
                    points=[(201, 201), (211, 201), (211, 211)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v2")],
                ),
                InputGeoOnderverdelingSpec(
                    key="lake_v2",
                    title="lake",
                    points=[(210, 210), (220, 210), (220, 220)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v2")],
                ),
                InputGeoOnderverdelingSpec(
                    key="river_v2",
                    title="river",
                    points=[(220, 220), (230, 220), (230, 230)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v2")],
                ),
                # Molens - mill B was removed
                InputGeoWerkingsgebiedenSpec(
                    key="mill_v2",
                    title="Molens",
                ),
                InputGeoOnderverdelingSpec(
                    title="mill A",
                    points=[(300, 300), (310, 300), (310, 310)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill_v2")],
                ),
                InputGeoOnderverdelingSpec(
                    title="mill C",
                    points=[(320, 320), (330, 320), (330, 330)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill_v2")],
                ),
            ]
        )
