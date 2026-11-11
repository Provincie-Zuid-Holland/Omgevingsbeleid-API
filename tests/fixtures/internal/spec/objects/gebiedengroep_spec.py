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
    __inheritable__: ClassVar[set[str]] = {"title", "description", "gebieden", "source_title", "source_uuid"}
    __object_fields__: ClassVar[set[str]] = {"title", "description", "gebieden", "source_title", "source_uuid"}
    __link_fields__: ClassVar[set[str]] = {"source_uuid"}

    title: str | None = None
    description: str | None = None
    gebieden: list[str] | None = None
    source_title: str | None = None
    source_uuid: Link | None = None


class GebiedengroepSpec(GebiedengroepMixin, BaseObjectSpec):
    pass


class GebiedengroepPrefillHandler(BaseObjectPrefillHandler[GebiedengroepSpec]):
    pass


class GebiedengroepPersistHandler(BaseObjectPersistHandler[GebiedengroepSpec]):
    pass
