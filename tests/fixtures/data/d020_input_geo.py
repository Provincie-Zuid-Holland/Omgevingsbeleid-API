import datetime

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import InputGeoWerkingsgebiedenSpec


def load(col: Collector) -> None:
    with col.with_defaults(
        Description="Herziening 2025 - Ontwerp GS Concept",
    ):
        col.adds(
            [
                # Natuur v1
                InputGeoWerkingsgebiedenSpec(
                    key="natuur-v1",
                    Title="Natuur",
                ),
                InputGeoOnderverdelingSpec(
                    Title="Natuur West",
                    Points=[(100, 100), (110, 100), (110, 110)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "natuur-v1")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Natuur Oost",
                    Points=[(110, 110), (120, 110), (120, 120)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "natuur-v1")],
                ),
                # Water v1
                InputGeoWerkingsgebiedenSpec(
                    key="water-v1",
                    Title="Water",
                ),
                InputGeoOnderverdelingSpec(
                    key="zee-1",
                    Title="Zee",
                    Points=[(200, 200), (210, 200), (210, 210)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v1")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Meer",
                    Points=[(210, 210), (220, 210), (220, 220)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v1")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Rivier",
                    Points=[(220, 220), (230, 220), (230, 230)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v1")],
                ),
                # Molens v1
                InputGeoWerkingsgebiedenSpec(
                    key="molen-v1",
                    Title="Molens",
                ),
                InputGeoOnderverdelingSpec(
                    Title="Molen A",
                    Points=[(300, 300), (310, 300), (310, 310)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "molen-v1")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Molen B",
                    Points=[(310, 310), (320, 310), (320, 320)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "molen-v1")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Molen C",
                    Points=[(320, 320), (330, 320), (330, 330)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "molen-v1")],
                ),
            ]
        )

    # Updated the Input Geo in februari
    with col.with_defaults(
        Created_Date=datetime.datetime(2025, 2, 1),
        Description="Herziening 2025 - Ontwerp GS",
    ):
        col.adds(
            [
                # Natuur - did not change
                InputGeoWerkingsgebiedenSpec(
                    key="natuur-v2",
                    Title="Natuur",
                ),
                InputGeoOnderverdelingSpec(
                    Title="Natuur West",
                    Points=[(100, 100), (110, 100), (110, 110)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "natuur-v2")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Natuur Oost",
                    Points=[(110, 110), (120, 110), (120, 120)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "natuur-v2")],
                ),
                # Water - Only the sea moved a bit
                InputGeoWerkingsgebiedenSpec(
                    key="water-v2",
                    Title="Water",
                ),
                InputGeoOnderverdelingSpec(
                    Title="Zee",
                    Points=[(201, 201), (211, 201), (211, 211)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v2")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Meer",
                    Points=[(210, 210), (220, 210), (220, 220)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v2")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Rivier",
                    Points=[(220, 220), (230, 220), (230, 230)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v2")],
                ),
                # Molens - Molen B was removed
                InputGeoWerkingsgebiedenSpec(
                    key="molen-v2",
                    Title="Molens",
                ),
                InputGeoOnderverdelingSpec(
                    Title="Molen A",
                    Points=[(300, 300), (310, 300), (310, 310)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "molen-v2")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Molen C",
                    Points=[(320, 320), (330, 320), (330, 330)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "molen-v2")],
                ),
            ]
        )

    # Updated the Input Geo in march
    with col.with_defaults(
        Created_Date=datetime.datetime(2025, 3, 1),
        Description="Herziening 2025 - Ter Inzage",
    ):
        col.adds(
            [
                # Natuur - We added a North
                InputGeoWerkingsgebiedenSpec(
                    key="natuur-v3",
                    Title="Natuur",
                ),
                InputGeoOnderverdelingSpec(
                    Title="Natuur West",
                    Points=[(100, 100), (110, 100), (110, 110)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "natuur-v3")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Natuur Oost",
                    Points=[(110, 110), (120, 110), (120, 120)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "natuur-v3")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Natuur Noord",
                    Points=[(120, 120), (130, 120), (130, 130)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "natuur-v3")],
                ),
                # Water - The sea moved again, and we removed the lakes
                InputGeoWerkingsgebiedenSpec(
                    key="water-v3",
                    Title="Water",
                ),
                InputGeoOnderverdelingSpec(
                    Title="Zee",
                    Points=[(202, 202), (212, 202), (212, 212)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v3")],
                ),
                InputGeoOnderverdelingSpec(
                    Title="Rivier",
                    Points=[(220, 220), (230, 220), (230, 230)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "water-v3")],
                ),
                # Molens - Molen A was removed
                InputGeoWerkingsgebiedenSpec(
                    key="molen-v3",
                    Title="Molens",
                ),
                InputGeoOnderverdelingSpec(
                    Title="Molen C",
                    Points=[(320, 320), (330, 320), (330, 330)],
                    Owners=[col.ref(InputGeoWerkingsgebiedenSpec, "molen-v3")],
                ),
            ]
        )
