from collections import defaultdict

import tests.fixtures.internal.spec.modules as module_types
import tests.fixtures.internal.spec.objects as objects_types
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.services.collector import Record
from tests.fixtures.internal.spec.area_spec import AreaPrefillHandler, AreaSpec
from tests.fixtures.internal.spec.asset_spec import AssetPrefillHandler, AssetSpec
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnPrefillHandler, HoofdlijnSpec
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import (
    InputGeoOnderverdelingPrefillHandler,
    InputGeoOnderverdelingSpec,
)
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import (
    InputGeoWerkingsgebiedenPrefillHandler,
    InputGeoWerkingsgebiedenSpec,
)
from tests.fixtures.internal.spec.object_related_file_spec import ObjectRelatedFilePrefillHandler, ObjectRelatedFileSpec
from tests.fixtures.internal.spec.storage_file_spec import StorageFilePrefillHandler, StorageFileSpec
from tests.fixtures.internal.spec.user_spec import UserPrefillHandler, UserSpec
from tests.fixtures.internal.types import Spec


class PrefillService[S: Spec, H: BasePrefillHandler]:
    def __init__(self):
        self._handlers: dict[type[S], H] = {
            # Base
            UserSpec: UserPrefillHandler(),
            AssetSpec: AssetPrefillHandler(),
            StorageFileSpec: StorageFilePrefillHandler(),
            ObjectRelatedFileSpec: ObjectRelatedFilePrefillHandler(),
            HoofdlijnSpec: HoofdlijnPrefillHandler(),
            # Geo
            InputGeoWerkingsgebiedenSpec: InputGeoWerkingsgebiedenPrefillHandler(),
            InputGeoOnderverdelingSpec: InputGeoOnderverdelingPrefillHandler(),
            AreaSpec: AreaPrefillHandler(),
            # Objects
            objects_types.BeleidsdoelSpec: objects_types.BeleidsdoelPrefillHandler(),
            objects_types.BeleidskeuzeSpec: objects_types.BeleidskeuzePrefillHandler(),
            objects_types.GebiedSpec: objects_types.GebiedPrefillHandler(),
            objects_types.GebiedengroepSpec: objects_types.GebiedengroepPrefillHandler(),
            objects_types.GebiedsaanwijzingSpec: objects_types.GebiedsaanwijzingPrefillHandler(),
            objects_types.MaatregelSpec: objects_types.MaatregelPrefillHandler(),
            # Module
            module_types.ModuleSpec: module_types.ModulePrefillHandler(),
            module_types.ModuleStatusHistorySpec: module_types.ModuleStatusHistoryPrefillHandler(),
            # Module Objects
            module_types.ModuleBeleidsdoelSpec: module_types.ModuleBeleidsdoelPrefillHandler(),
            module_types.ModuleBeleidskeuzeSpec: module_types.ModuleBeleidskeuzePrefillHandler(),
            module_types.ModuleGebiedSpec: module_types.ModuleGebiedPrefillHandler(),
            module_types.ModuleGebiedengroepSpec: module_types.ModuleGebiedengroepPrefillHandler(),
            module_types.ModuleGebiedsaanwijzingSpec: module_types.ModuleGebiedsaanwijzingPrefillHandler(),
            module_types.ModuleMaatregelSpec: module_types.ModuleMaatregelPrefillHandler(),
        }

    def prefill(self, input_records: list[Record]) -> list[Record]:
        spec_counter: dict[type[Spec], int] = defaultdict(int)
        output: list[Record] = []

        for input_record in input_records:
            spec_type: type[S] = type(input_record.spec)
            spec_counter[spec_type] += 1
            current_spec_count = spec_counter[spec_type]

            handler: H | None = self._handlers.get(spec_type)
            if handler is None:
                raise RuntimeError(f"No prefill handler for {type(input_record.spec)}")

            input_record = handler.fill(
                input_record,
                PrefillContext(
                    previous_records=output,
                    spec_count=current_spec_count,
                ),
            )

            output.append(input_record)

        return output
