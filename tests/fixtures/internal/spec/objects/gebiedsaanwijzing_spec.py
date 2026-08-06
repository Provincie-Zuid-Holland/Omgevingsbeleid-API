from typing import ClassVar, List, Optional, Set

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectSpec,
    BaseObjectPrefillHandler,
)


class GebiedsaanwijzingMixin(BaseModel):
    __object_type__: ClassVar[str] = "gebiedsaanwijzing"
    __inheritable__: ClassVar[Set[str]] = {"Title", "Ref_Type", "Ref_Group", "Target_Codes"}
    __object_fields__: ClassVar[Set[str]] = {"Title", "Ref_Type", "Ref_Group", "Target_Codes"}

    Title: Optional[str] = None
    Ref_Type: Optional[str] = None
    Ref_Group: Optional[str] = None
    Target_Codes: Optional[List[str]] = None


class GebiedsaanwijzingSpec(GebiedsaanwijzingMixin, BaseObjectSpec):
    pass


class GebiedsaanwijzingPrefillHandler(BaseObjectPrefillHandler[GebiedsaanwijzingSpec]):
    pass


class GebiedsaanwijzingPersistHandler(BaseObjectPersistHandler[GebiedsaanwijzingSpec]):
    pass
