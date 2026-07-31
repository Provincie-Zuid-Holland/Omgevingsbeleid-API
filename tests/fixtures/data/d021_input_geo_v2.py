import datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import InputGeoWerkingsgebiedenSpec


def load(col: Collector) -> None:
    # Updated the Input Geo in februari
    with col.with_defaults(
        Created_Date=datetime.datetime(2025, 2, 1),
        Description="Herziening 2025 - Ontwerp GS",
    ):
        col.adds(
            [
                # Nature - did not change
                InputGeoWerkingsgebiedenSpec(
                    key="nature-v2",
                    Title="Nature",
                ),
                InputGeoOnderverdelingSpec(
                    key="nature-west-v2",
                    Title="Nature West",
                    Points=[(100, 100), (110, 100), (110, 110)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature-v2")],
                ),
                InputGeoOnderverdelingSpec(
                    key="nature-east-v2",
                    Title="Nature east",
                    Points=[(110, 110), (120, 110), (120, 120)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature-v2")],
                ),
                # Water - Only the sea moved a bit
                InputGeoWerkingsgebiedenSpec(
                    key="water-v2",
                    Title="Water",
                ),
                InputGeoOnderverdelingSpec(
                    key="sea-v2",
                    Title="sea",
                    Points=[(201, 201), (211, 201), (211, 211)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v2")],
                ),
                InputGeoOnderverdelingSpec(
                    key="lake-v2",
                    Title="lake",
                    Points=[(210, 210), (220, 210), (220, 220)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v2")],
                ),
                InputGeoOnderverdelingSpec(
                    key="river-v2",
                    Title="river",
                    Points=[(220, 220), (230, 220), (230, 230)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v2")],
                ),
                # Molens - mill B was removed
                InputGeoWerkingsgebiedenSpec(
                    key="mill-v2",
                    Title="Molens",
                ),
                InputGeoOnderverdelingSpec(
                    Title="mill A",
                    Points=[(300, 300), (310, 300), (310, 310)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill-v2")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="mill C",
                    Points=[(320, 320), (330, 320), (330, 330)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill-v2")],
                ),
            ]
        )
