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
                    title="Nature",
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_west_v1",
                    title="Nature West",
                    points=[(100, 100), (110, 100), (110, 110)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_east_v1",
                    title="Nature east",
                    points=[(110, 110), (120, 110), (120, 120)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    key="nature_south_v1",
                    title="Nature south",
                    points=[(130, 130), (140, 130), (140, 140)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "nature_v1")],
                ),
                # Water v1
                InputGeoWerkingsgebiedenSpec(
                    key="water_v1",
                    title="Water",
                ),
                InputGeoOnderverdelingSpec(
                    key="sea_v1",
                    title="sea",
                    points=[(200, 200), (210, 200), (210, 210)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    key="lake_v1",
                    title="lake",
                    points=[(210, 210), (220, 210), (220, 220)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    key="river_v1",
                    title="river",
                    points=[(220, 220), (230, 220), (230, 230)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water_v1")],
                ),
                # Molens v1
                InputGeoWerkingsgebiedenSpec(
                    key="mill_v1",
                    title="Molens",
                ),
                InputGeoOnderverdelingSpec(
                    title="mill A",
                    points=[(300, 300), (310, 300), (310, 310)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    title="mill B",
                    points=[(310, 310), (320, 310), (320, 320)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill_v1")],
                ),
                InputGeoOnderverdelingSpec(
                    title="mill C",
                    points=[(320, 320), (330, 320), (330, 330)],
                    owners=[col.ref(InputGeoWerkingsgebiedenSpec, "mill_v1")],
                ),
            ]
        )
