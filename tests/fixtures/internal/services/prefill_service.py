from collections import defaultdict
from typing import List, Dict, Optional, Type

from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.services.collector import Record
from tests.fixtures.internal.spec.asset_spec import AssetPrefillHandler, AssetSpec
from tests.fixtures.internal.spec.storage_file_spec import StorageFilePrefillHandler, StorageFileSpec
from tests.fixtures.internal.spec.user_spec import UserPrefillHandler, UserSpec
from tests.fixtures.internal.spec.objects.ambitie_spec import AmbitiePrefillHandler, AmbitieSpec
from tests.fixtures.internal.types import Spec


class PrefillService[S: Spec, H: BasePrefillHandler]:
    def __init__(self):
        self._handlers: Dict[Type[S], H] = {
            UserSpec: UserPrefillHandler(),
            AssetSpec: AssetPrefillHandler(),
            StorageFileSpec: StorageFilePrefillHandler(),
            AmbitieSpec: AmbitiePrefillHandler(),
        }

    def prefill(self, input_records: List[Record]) -> List[Record]:
        spec_counter: Dict[Type[S], int] = defaultdict(int)
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
