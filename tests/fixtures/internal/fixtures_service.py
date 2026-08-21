from collections.abc import Callable

from sqlalchemy.orm import Session

from tests.fixtures.data import (
    d001_users,
    d002_assets,
    d003_storage_files,
    d020_input_geo_v1,
    d021_input_geo_v2,
    d022_input_geo_v3,
    d030_areas,
    d050_objects_january,
    d060_objects_february,
    d070_objects_march,
    d080_objects_2099,
    d101_object_related_files,
    d102_hoofdlijnen,
    d201_module_1_basic,
    d202_module_2_inactive,
    d203_module_3_closed,
    d204_module_4_ambtenaar_managed,
    d205_module_5_patch_module_1,
    d206_module_6_patch_module_2,
)
from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.services.linker_service import LinkerService
from tests.fixtures.internal.services.persist_service import PersistService
from tests.fixtures.internal.services.prefill_service import PrefillService
from tests.fixtures.internal.spec.user_spec import UserSpec
from tests.fixtures.internal.types import DATETIME_T0, FixtureData


class FixturesService:
    def load(self, session: Session):
        sources: list[Callable[[Collector], None]] = [
            d001_users.load,
            d002_assets.load,
            d003_storage_files.load,
            d020_input_geo_v1.load,
            d021_input_geo_v2.load,
            d022_input_geo_v3.load,
            d030_areas.load,
            d050_objects_january.load,
            d060_objects_february.load,
            d070_objects_march.load,
            d080_objects_2099.load,
            d101_object_related_files.load,
            d102_hoofdlijnen.load,
            d201_module_1_basic.load,
            d202_module_2_inactive.load,
            d203_module_3_closed.load,
            d204_module_4_ambtenaar_managed.load,
            d205_module_5_patch_module_1.load,
            d206_module_6_patch_module_2.load,
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
