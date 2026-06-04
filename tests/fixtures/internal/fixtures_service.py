from typing import Callable, List

from sqlalchemy.orm import Session

from tests.fixtures.internal.types import DATETIME_T0, FixtureData
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.services.linker_service import LinkerService
from tests.fixtures.internal.services.persist_service import PersistService
from tests.fixtures.internal.services.prefill_service import PrefillService
import tests.fixtures.data.d001_users as d001_users
import tests.fixtures.data.d002_assets as d002_assets
import tests.fixtures.data.d003_storage_files as d003_storage_files
import tests.fixtures.data.d020_input_geo as d020_input_geo

# import tests.fixtures.data.d050_basic_demo as d050_basic_demo
from tests.fixtures.internal.spec.user_spec import UserSpec


class FixturesService:
    def load(self, session: Session):
        sources: List[Callable[[Collector], None]] = [
            d001_users.load,
            d002_assets.load,
            d003_storage_files.load,
            d020_input_geo.load,
        ]

        collector: Collector = Collector()
        for source in sources:
            collector.at(DATETIME_T0)
            with collector.with_defaults(
                Created_By_UUID=collector.ref(UserSpec, "admin"),
                Modified_By_UUID=collector.ref(UserSpec, "admin"),
            ):
                source(collector)

        result = collector.get_results()

        prefill: PrefillService = PrefillService()
        result = prefill.prefill(result)

        linker: LinkerService = LinkerService()
        result = linker.link(result)

        persister: PersistService = PersistService()
        fixture_data: FixtureData = persister.persist(result, session)

        return fixture_data
