from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.area_spec import AreaSpec
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec


def load(col: Collector) -> None:
    col.adds(
        [
            AreaSpec(
                key="nature-west-v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "nature-west-v1"),
            ),
            AreaSpec(
                key="nature-east-v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "nature-east-v1"),
            ),
        ]
    )

    col.adds(
        [
            AreaSpec(
                key="sea-v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "sea-v1"),
            ),
            AreaSpec(
                key="lake-v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "lake-v1"),
            ),
            AreaSpec(
                key="river-v1",
                Source_Ref=col.ref(InputGeoOnderverdelingSpec, "river-v1"),
            ),
        ]
    )
