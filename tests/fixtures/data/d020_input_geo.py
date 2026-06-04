from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import InputGeoWerkingsgebiedenSpec


def load(col: Collector) -> None:
    # Ontwerp GS Concept
    # Ontwerp GS
    # Ter Inzage
    with col.with_defaults(
        Description="Herziening 2025 - Ontwerp GS Concept",
    ):
        col.adds(
            [
                InputGeoWerkingsgebiedenSpec(
                    key="natuur-1",
                    Title="Natuur",
                ),
                InputGeoOnderverdelingSpec(
                    Title="Natuur West",
                    Points=[(100, 100), (110, 100), (110, 110)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "natuur-1")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Natuur Oost",
                    Points=[(200, 200), (210, 200), (210, 210)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "natuur-1")],
                ),
            ]
        )
