
from typing import Any, List, Dict, Optional, Type

from tests.fixtures.internal.services.collector import Record
from tests.fixtures.internal.types import Ref, Spec, PrimaryKey


class LinkerService[T: Spec]:
    def __init__(self):
        pass

    def link(self, records: List[Record[T]]) -> List[Record[T]]:
        ref_cache: Dict[Ref, PrimaryKey] = self._build_ref_cache(records)

        for input_record in records:
            for field_name in input_record.spec.get_link_fields():
                field_value: Any = getattr(input_record.spec, field_name)
                if isinstance(field_value, Ref):
                    resolved_ref: Optional[PrimaryKey] = ref_cache.get(field_value)
                    if resolved_ref is None:
                        raise RuntimeError("Ref to unknown item")
                    setattr(input_record.spec, field_name, resolved_ref)

        return records

    def _build_ref_cache(self, input_records: List[Record[T]]) -> Dict[Ref, PrimaryKey]:
        ref_cache: Dict[Ref, PrimaryKey] = {}

        for input_record in input_records:
            if input_record.spec.key is not None:
                spec_type: Type[T] = type(input_record.spec)
                ref: Ref = Ref(spec_type, input_record.spec.key)
                ref_cache[ref] = input_record.spec.get_table_primary_key()
        
        return ref_cache
