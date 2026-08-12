from datetime import UTC, datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import InputGeoWerkingsgebiedenSpec


def load(col: Collector) -> None:
    # Updated the Input Geo in march
    with col.with_defaults(
        Created_Date=datetime(2025, 3, 1, tzinfo=UTC),
        Description="Herziening 2025 - Ter Inzage",
    ):
        col.adds(
            [
                # Nature - We added a North
                InputGeoWerkingsgebiedenSpec(
                    key="nature-v3",
                    Title="Nature",
                ),
                InputGeoOnderverdelingSpec(
                    key="nature-west-v3",
                    Title="Nature West",
                    Points=[(100, 100), (110, 100), (110, 110)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature-v3")],
                ),
                InputGeoOnderverdelingSpec(
                    key="nature-east-v3",
                    Title="Nature east",
                    Points=[(110, 110), (120, 110), (120, 120)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature-v3")],
                ),
                InputGeoOnderverdelingSpec(
                    key="nature-noord-v3",
                    Title="Nature Noord",
                    Points=[(120, 120), (130, 120), (130, 130)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature-v3")],
                ),
                # Water - The sea moved again, and we removed the lakes
                InputGeoWerkingsgebiedenSpec(
                    key="water-v3",
                    Title="Water",
                ),
                InputGeoOnderverdelingSpec(
                    Title="sea",
                    key="sea-v3",
                    Points=[(202, 202), (212, 202), (212, 212)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v3")],
                ),
                InputGeoOnderverdelingSpec(
                    key="river-v3",
                    Title="river",
                    Points=[(220, 220), (230, 220), (230, 230)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v3")],
                ),
                # Molens - mill A was removed
                InputGeoWerkingsgebiedenSpec(
                    key="mill-v3",
                    Title="Molens",
                ),
                InputGeoOnderverdelingSpec(
                    Title="mill C",
                    Points=[(320, 320), (330, 320), (330, 330)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill-v3")],
                ),
            ]
        )
