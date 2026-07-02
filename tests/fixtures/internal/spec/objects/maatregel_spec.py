from typing import ClassVar, Optional, Set

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectSpec,
    BaseObjectPrefillHandler,
)


class MaatregelMixin(BaseModel):
    __object_type__: ClassVar[str] = "maatregel"
    __inheritable__: ClassVar[Set[str]] = {"Title", "Description", "Effect", "Hierarchy_Code", "Gebiedengroep_Code"}
    __object_fields__: ClassVar[Set[str]] = {"Title", "Description", "Effect", "Hierarchy_Code", "Gebiedengroep_Code"}

    Title: Optional[str] = None
    Description: Optional[str] = None
    Effect: Optional[str] = None
    Hierarchy_Code: Optional[str] = None
    Gebiedengroep_Code: Optional[str] = None


class MaatregelSpec(MaatregelMixin, BaseObjectSpec):
    pass


class MaatregelPrefillHandler(BaseObjectPrefillHandler[MaatregelSpec]):
    pass


class MaatregelPersistHandler(BaseObjectPersistHandler[MaatregelSpec]):
    pass
