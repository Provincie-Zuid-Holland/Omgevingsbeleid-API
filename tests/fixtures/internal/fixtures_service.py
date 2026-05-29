from rich import print as pprint

from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.services.linker_service import LinkerService
from tests.fixtures.internal.services.prefill_service import PrefillService
import tests.fixtures.data.d001_users as d001_users
import tests.fixtures.data.d050_basic as d050_basic


class FixturesService:
    def __init__(self):
        pass

    def load(self):
        collector: Collector = Collector()
        d001_users.load(collector)
        d050_basic.load(collector)
        result = collector.get_results()

        prefill: PrefillService = PrefillService()
        result = prefill.prefill(result)

        linker: LinkerService = LinkerService()
        result = linker.link(result)

        print("\n\n")
        pprint(result)
