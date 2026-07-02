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
import tests.fixtures.data.d021_areas as d021_areas
import tests.fixtures.data.d050_objects_january as d050_objects_january
import tests.fixtures.data.d060_objects_february as d060_objects_february
import tests.fixtures.data.d070_objects_march as d070_objects_march
import tests.fixtures.data.d080_objects_2099 as d080_objects_2099
import tests.fixtures.data.d201_module_1_basic as d201_module_1_basic
import tests.fixtures.data.d202_module_2_inactive as d202_module_2_inactive
import tests.fixtures.data.d203_module_3_closed as d203_module_3_closed
import tests.fixtures.data.d204_module_4_ambtenaar_managed as d204_module_4_ambtenaar_managed

# import tests.fixtures.data.d050_basic_demo as d050_basic_demo
from tests.fixtures.internal.spec.user_spec import UserSpec


class FixturesService:
    def load(self, session: Session):
        sources: List[Callable[[Collector], None]] = [
            d001_users.load,
            d002_assets.load,
            d003_storage_files.load,
            d020_input_geo.load,
            d021_areas.load,
            d050_objects_january.load,
            d060_objects_february.load,
            d070_objects_march.load,
            d080_objects_2099.load,
            d201_module_1_basic.load,
            d202_module_2_inactive.load,
            d203_module_3_closed.load,
            d204_module_4_ambtenaar_managed.load,
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
