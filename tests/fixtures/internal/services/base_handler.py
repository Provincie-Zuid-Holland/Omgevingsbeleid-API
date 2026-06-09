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
        for field_name, default_value in record.ctx.defaults.items():
            if field_name in type(record.spec).model_fields:
                if field_name not in record.spec.model_fields_set:
                    setattr(record.spec, field_name, default_value)

        return record
