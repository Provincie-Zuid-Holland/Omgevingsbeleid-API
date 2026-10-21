from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import InputGeoWerkingsgebiedenSpec


def load(col: Collector) -> None:
    # Updated the Input Geo in March
    with col.with_defaults(
        created_date=datetime(2025, 3, 1, tzinfo=UTC),
        Description="Herziening 2025 - Ter Inzage",
    ):
        col.adds(
            [
                # Nature - We added a North
                InputGeoWerkingsgebiedenSpec(
                    key="nature_v3",
                    title="Nature",
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_west_v3",
                    title="Nature West",
                    points=[(100, 100), (110, 100), (110, 110)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v3")],
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_east_v3",
                    title="Nature east",
                    points=[(110, 110), (120, 110), (120, 120)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v3")],
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_noord_v3",
                    title="Nature Noord",
                    points=[(120, 120), (130, 120), (130, 130)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v3")],
                ),
                # Water - The sea moved again, and we removed the lakes
                InputGeoWerkingsgebiedenSpec(
                    key="water_v3",
                    title="Water",
                ),
                InputGeoOnderverdelingSpec(
                    title="sea",
                    key="sea_v3",
                    points=[(202, 202), (212, 202), (212, 212)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v3")],
                ),
                InputGeoOnderverdelingSpec(
                    key="river_v3",
                    title="river",
                    points=[(220, 220), (230, 220), (230, 230)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v3")],
                ),
                # Molens - mill A was removed
                InputGeoWerkingsgebiedenSpec(
                    key="mill_v3",
                    title="Molens",
                ),
                InputGeoOnderverdelingSpec(
                    title="mill C",
                    points=[(320, 320), (330, 320), (330, 330)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill_v3")],
                ),
            ]
        )
