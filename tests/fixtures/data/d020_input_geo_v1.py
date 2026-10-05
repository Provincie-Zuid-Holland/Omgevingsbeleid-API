from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import InputGeoWerkingsgebiedenSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Description="Herziening 2025 - Ontwerp GS Concept",
    ):
        col.adds(
            [
                # Nature v1
                InputGeoWerkingsgebiedenSpec(
                    key="nature_v1",
                    Title="Nature",
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_west_v1",
                    Title="Nature West",
                    Points=[(100, 100), (110, 100), (110, 110)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_east_v1",
                    Title="Nature east",
                    Points=[(110, 110), (120, 110), (120, 120)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_south_v1",
                    Title="Nature south",
                    Points=[(130, 130), (140, 130), (140, 140)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v1")],
                ),
                # Water v1
                InputGeoWerkingsgebiedenSpec(
                    key="water_v1",
                    Title="Water",
                ),
                InputGeoOnderverdelingSpec(
                    key="sea_v1",
                    Title="sea",
                    Points=[(200, 200), (210, 200), (210, 210)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    key="lake_v1",
                    Title="lake",
                    Points=[(210, 210), (220, 210), (220, 220)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    key="river_v1",
                    Title="river",
                    Points=[(220, 220), (230, 220), (230, 230)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v1")],
                ),
                # Molens v1
                InputGeoWerkingsgebiedenSpec(
                    key="mill_v1",
                    Title="Molens",
                ),
                InputGeoOnderverdelingSpec(
                    Title="mill A",
                    Points=[(300, 300), (310, 300), (310, 310)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="mill B",
                    Points=[(310, 310), (320, 310), (320, 320)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="mill C",
                    Points=[(320, 320), (330, 320), (330, 330)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill_v1")],
                ),
            ]
        )
