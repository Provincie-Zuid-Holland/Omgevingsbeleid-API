from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.area_spec import AreaSpec
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec


def load(col: Collector) -> None:
    col.adds(
        [
            AreaSpec(
                key="nature_west_v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "nature_west_v1"),
            ),
            AreaSpec(
                key="nature_east_v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "nature_east_v1"),
            ),
            AreaSpec(
                key="nature_south_v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "nature_south_v1"),
            ),
        ]
    )

    col.adds(
        [
            AreaSpec(
                key="sea_v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "sea_v1"),
            ),
            AreaSpec(
                key="lake_v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "lake_v1"),
            ),
            AreaSpec(
                key="river_v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "river_v1"),
            ),
        ]
    )
