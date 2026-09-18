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
    __inheritable__: ClassVar[set[str]] = {"Title", "area_id"}
    __object_fields__: ClassVar[set[str]] = {"Title", "area_id"}
    __link_fields__: ClassVar[set[str]] = {"area_id"}

    Title: str | None = None
    area_id: Link | None = None


class GebiedSpec(GebiedMixin, BaseObjectSpec):
    pass


class GebiedPrefillHandler(BaseObjectPrefillHandler[GebiedSpec]):
    pass


class GebiedPersistHandler(BaseObjectPersistHandler[GebiedSpec]):
    pass
