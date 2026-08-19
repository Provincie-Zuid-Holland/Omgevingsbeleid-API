from typing import ClassVar

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectPrefillHandler,
    BaseObjectSpec,
)
from tests.fixtures.internal.types import Link


class GebiedMixin(BaseModel):
    __object_type__: ClassVar[str] = "gebied"
    __inheritable__: ClassVar[set[str]] = {"Title", "Area_UUID"}
    __object_fields__: ClassVar[set[str]] = {"Title", "Area_UUID"}
    __link_fields__: ClassVar[set[str]] = {"Area_UUID"}

    Title: str | None = None
    Area_UUID: Link | None = None


class GebiedSpec(GebiedMixin, BaseObjectSpec):
    pass


class GebiedPrefillHandler(BaseObjectPrefillHandler[GebiedSpec]):
    pass


class GebiedPersistHandler(BaseObjectPersistHandler[GebiedSpec]):
    pass
