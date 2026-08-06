from typing import ClassVar, List, Optional, Set

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectSpec,
    BaseObjectPrefillHandler,
)
from tests.fixtures.internal.types import Link


class GebiedengroepMixin(BaseModel):
    __object_type__: ClassVar[str] = "gebiedengroep"
    __inheritable__: ClassVar[Set[str]] = {"Title", "Description", "Gebieden", "Source_Title", "Source_UUID"}
    __object_fields__: ClassVar[Set[str]] = {"Title", "Description", "Gebieden", "Source_Title", "Source_UUID"}
    __link_fields__: ClassVar[Set[str]] = {"Source_UUID"}

    Title: Optional[str] = None
    Description: Optional[str] = None
    Gebieden: Optional[List[str]] = None
    Source_Title: Optional[str] = None
    Source_UUID: Optional[Link] = None


class GebiedengroepSpec(GebiedengroepMixin, BaseObjectSpec):
    pass


class GebiedengroepPrefillHandler(BaseObjectPrefillHandler[GebiedengroepSpec]):
    pass


class GebiedengroepPersistHandler(BaseObjectPersistHandler[GebiedengroepSpec]):
    pass
