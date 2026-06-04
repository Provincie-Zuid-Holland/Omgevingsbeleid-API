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
                if isinstance(field_value, list):
                    resolved_value = [self._resolve(field_name, item, ref_cache) for item in field_value]
                else:
                    resolved_value = self._resolve(field_name, field_value, ref_cache)
                setattr(input_record.spec, field_name, resolved_value)

        return records

    def _resolve(self, field_name: str, value: Any, ref_cache: Dict[Ref, PrimaryKey]) -> Any:
        if not isinstance(value, Ref):
            return value
        resolved: Optional[PrimaryKey] = ref_cache.get(value)
        if resolved is None:
            raise RuntimeError(f"Unresolved Ref on field '{field_name}': {value!r}")
        return resolved

    def _build_ref_cache(self, input_records: List[Record[T]]) -> Dict[Ref, PrimaryKey]:
        ref_cache: Dict[Ref, PrimaryKey] = {}

        for input_record in input_records:
            if input_record.spec.key is not None:
                spec_type: Type[T] = type(input_record.spec)
                ref: Ref = Ref(spec_type, input_record.spec.key)
                ref_cache[ref] = input_record.spec.get_table_primary_key()

        return ref_cache
