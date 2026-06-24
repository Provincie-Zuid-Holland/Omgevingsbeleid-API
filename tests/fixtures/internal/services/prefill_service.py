from collections import defaultdict
from typing import List, Dict, Optional, Type

from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.services.collector import Record
from tests.fixtures.internal.spec.area_spec import AreaPrefillHandler, AreaSpec
from tests.fixtures.internal.spec.asset_spec import AssetPrefillHandler, AssetSpec
from tests.fixtures.internal.spec.input_geo_onderverdeling_spec import (
    InputGeoOnderverdelingPrefillHandler,
    InputGeoOnderverdelingSpec,
)
from tests.fixtures.internal.spec.input_geo_werkingsgebied_spec import (
    InputGeoWerkingsgebiedenPrefillHandler,
    InputGeoWerkingsgebiedenSpec,
)
from tests.fixtures.internal.spec.storage_file_spec import StorageFilePrefillHandler, StorageFileSpec
from tests.fixtures.internal.spec.user_spec import UserPrefillHandler, UserSpec
import tests.fixtures.internal.spec.objects as objects_types
from tests.fixtures.internal.spec.modules import (
    ModuleSpec,
    ModulePrefillHandler,
    ModuleStatusHistorySpec,
    ModuleStatusHistoryPrefillHandler,
    ModuleBeleidsdoelSpec,
    ModuleBeleidsdoelPrefillHandler,
    ModuleBeleidskeuzeSpec,
    ModuleBeleidskeuzePrefillHandler,
    ModuleMaatregelSpec,
    ModuleMaatregelPrefillHandler,
)
from tests.fixtures.internal.types import Spec


class PrefillService[S: Spec, H: BasePrefillHandler]:
    def __init__(self):
        self._handlers: Dict[Type[S], H] = {
            UserSpec: UserPrefillHandler(),
            AssetSpec: AssetPrefillHandler(),
            StorageFileSpec: StorageFilePrefillHandler(),
            objects_types.BeleidsdoelSpec: objects_types.BeleidsdoelPrefillHandler(),
            objects_types.BeleidskeuzeSpec: objects_types.BeleidskeuzePrefillHandler(),
            objects_types.MaatregelSpec: objects_types.MaatregelPrefillHandler(),
            InputGeoWerkingsgebiedenSpec: InputGeoWerkingsgebiedenPrefillHandler(),
            InputGeoOnderverdelingSpec: InputGeoOnderverdelingPrefillHandler(),
            AreaSpec: AreaPrefillHandler(),
            ModuleSpec: ModulePrefillHandler(),
            ModuleStatusHistorySpec: ModuleStatusHistoryPrefillHandler(),
            ModuleBeleidsdoelSpec: ModuleBeleidsdoelPrefillHandler(),
            ModuleBeleidskeuzeSpec: ModuleBeleidskeuzePrefillHandler(),
            ModuleMaatregelSpec: ModuleMaatregelPrefillHandler(),
        }

    def prefill(self, input_records: List[Record]) -> List[Record]:
        spec_counter: Dict[Type[Spec], int] = defaultdict(int)
        output: List[Record] = []

        for input_record in input_records:
            spec_type: Type[S] = type(input_record.spec)
            spec_counter[spec_type] += 1
            current_spec_count = spec_counter[spec_type]

            handler: Optional[H] = self._handlers.get(spec_type)
            if handler:
                input_record = handler.fill(
                    input_record,
                    PrefillContext(
                        previous_records=output,
                        spec_count=current_spec_count,
                    ),
                )

            output.append(input_record)

        return output
