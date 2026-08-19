from typing import ClassVar

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectPrefillHandler,
    BaseObjectSpec,
)
from tests.fixtures.internal.types import Link


class GebiedengroepMixin(BaseModel):
    __object_type__: ClassVar[str] = "gebiedengroep"
    __inheritable__: ClassVar[set[str]] = {"Title", "Description", "Gebieden", "Source_Title", "Source_UUID"}
    __object_fields__: ClassVar[set[str]] = {"Title", "Description", "Gebieden", "Source_Title", "Source_UUID"}
    __link_fields__: ClassVar[set[str]] = {"Source_UUID"}

    Title: str | None = None
    Description: str | None = None
    Gebieden: list[str] | None = None
    Source_Title: str | None = None
    Source_UUID: Link | None = None


class GebiedengroepSpec(GebiedengroepMixin, BaseObjectSpec):
    pass


class GebiedengroepPrefillHandler(BaseObjectPrefillHandler[GebiedengroepSpec]):
    pass


class GebiedengroepPersistHandler(BaseObjectPersistHandler[GebiedengroepSpec]):
    pass
