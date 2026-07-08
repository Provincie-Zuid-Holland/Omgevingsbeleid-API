from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.area_spec import AreaSpec
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import InputGeoOnderverdelingSpec


def load(col: Collector) -> None:
    col.adds([AreaSpec(Source_Ref=col.ref(InputGeoOnderverdelingSpec, "zee-1"))])
