from typing import ClassVar

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectPrefillHandler,
    BaseObjectSpec,
)


class GebiedsaanwijzingMixin(BaseModel):
    __object_type__: ClassVar[str] = "gebiedsaanwijzing"
    __inheritable__: ClassVar[set[str]] = {"Title", "Ref_Type", "Ref_Group", "Target_Codes"}
    __object_fields__: ClassVar[set[str]] = {"Title", "Ref_Type", "Ref_Group", "Target_Codes"}

    Title: str | None = None
    Ref_Type: str | None = None
    Ref_Group: str | None = None
    Target_Codes: list[str] | None = None


class GebiedsaanwijzingSpec(GebiedsaanwijzingMixin, BaseObjectSpec):
    pass


class GebiedsaanwijzingPrefillHandler(BaseObjectPrefillHandler[GebiedsaanwijzingSpec]):
    pass


class GebiedsaanwijzingPersistHandler(BaseObjectPersistHandler[GebiedsaanwijzingSpec]):
    pass
