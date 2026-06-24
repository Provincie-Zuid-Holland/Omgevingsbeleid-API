from copy import copy
from typing import List, Optional

from pydantic import BaseModel

from tests.fixtures.internal.types import Record, Spec, Ref


class PrefillContext(BaseModel):
    previous_records: List[Record[Spec]]
    spec_count: int

    def find_optional(self, ref: Ref) -> Optional[Record[Spec]]:
        for record in self.previous_records:
            if type(record.spec) is not ref.spec_type:
                continue
            if record.spec.key != ref.key:
                continue
            return record
        return None

    def find(self, ref: Ref) -> Record[Spec]:
        result: Optional[Record[Spec]] = self.find_optional(ref)
        if result is None:
            raise RuntimeError(f"Could not find record for ref {ref!r}")
        return result


class BasePrefillHandler[T: Spec]:
    def fill(self, record: Record[T], context: PrefillContext) -> Record[T]:
        record = self._handle_default_context(record)
        record = self._handle_module_context(record)
        return record

    def _handle_default_context(self, record: Record[T]) -> Record[T]:
        for field_name, default_value in record.ctx.defaults.items():
            # Default value None is special and act like it does not exists
            # Therefor we wont use it to set the default value
            if default_value is None:
                continue

            if field_name in type(record.spec).model_fields:
                if field_name not in record.spec.model_fields_set:
                    setattr(record.spec, field_name, copy(default_value))
        return record

    def _handle_module_context(self, record: Record[T]) -> Record[T]:
        if record.ctx.module is None:
            return record
        if not hasattr(record.spec, "Module_ID"):
            return record
        if getattr(record.spec, "Module_ID"):
            return record

        setattr(record.spec, "Module_ID", record.ctx.module)
        return record
