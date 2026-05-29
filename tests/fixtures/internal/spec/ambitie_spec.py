from typing import ClassVar, Optional, Set

from tests.fixtures.internal.services.base_handler import PrefillContext
from tests.fixtures.internal.spec.base_object_spec import BaseObjectSpec, BaseObjectPrefillHandler
from tests.fixtures.internal.types import Record


class AmbitieSpec(BaseObjectSpec):
    __object_type__: ClassVar[str] = "ambitie"
    __inheritable__: ClassVar[Set[str]] = {"Title", "Description"}
    
    Title: Optional[str] = None
    Description: Optional[str] = None


class AmbitiePrefillHandler(BaseObjectPrefillHandler[AmbitieSpec]):
    def fill(self, record: Record[AmbitieSpec], context: PrefillContext) -> Record[AmbitieSpec]:
        record = super().fill(record, context)
        return record
