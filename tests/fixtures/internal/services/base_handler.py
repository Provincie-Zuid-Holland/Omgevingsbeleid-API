
from typing import List

from pydantic import BaseModel

from tests.fixtures.internal.types import Record, Spec


class PrefillContext(BaseModel):
    previous_records: List[Record[Spec]]
    spec_count: int



class BasePrefillHandler[T: Spec]:
    def fill(self, record: Record[T], context: PrefillContext) -> Record[T]:
        for field_name, default_value in record.ctx.defaults.items():
            if field_name in record.spec_type.model_fields:
                if field_name not in record.spec.model_fields_set:
                    setattr(record.spec, field_name, default_value)

        return record
