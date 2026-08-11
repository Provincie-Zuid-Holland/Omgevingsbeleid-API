from typing import ClassVar

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectPrefillHandler,
    BaseObjectSpec,
)


class MaatregelMixin(BaseModel):
    __object_type__: ClassVar[str] = "maatregel"
    __inheritable__: ClassVar[set[str]] = {"Title", "Description", "Effect", "Hierarchy_Code", "Gebiedengroep_Code"}
    __object_fields__: ClassVar[set[str]] = {"Title", "Description", "Effect", "Hierarchy_Code", "Gebiedengroep_Code"}

    Title: str | None = None
    Description: str | None = None
    Effect: str | None = None
    Hierarchy_Code: str | None = None
    Gebiedengroep_Code: str | None = None


class MaatregelSpec(MaatregelMixin, BaseObjectSpec):
    pass


class MaatregelPrefillHandler(BaseObjectPrefillHandler[MaatregelSpec]):
    pass


class MaatregelPersistHandler(BaseObjectPersistHandler[MaatregelSpec]):
    pass
