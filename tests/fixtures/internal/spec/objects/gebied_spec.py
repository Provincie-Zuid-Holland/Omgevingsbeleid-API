from typing import ClassVar, Optional, Set

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectSpec,
    BaseObjectPrefillHandler,
)
from tests.fixtures.internal.types import Link


class GebiedMixin(BaseModel):
    __object_type__: ClassVar[str] = "gebied"
    __inheritable__: ClassVar[Set[str]] = {"Title", "Area_UUID"}
    __object_fields__: ClassVar[Set[str]] = {"Title", "Area_UUID"}
    __link_fields__: ClassVar[Set[str]] = {"Area_UUID"}

    Title: Optional[str] = None
    Area_UUID: Optional[Link] = None


class GebiedSpec(GebiedMixin, BaseObjectSpec):
    pass


class GebiedPrefillHandler(BaseObjectPrefillHandler[GebiedSpec]):
    pass


class GebiedPersistHandler(BaseObjectPersistHandler[GebiedSpec]):
    pass
