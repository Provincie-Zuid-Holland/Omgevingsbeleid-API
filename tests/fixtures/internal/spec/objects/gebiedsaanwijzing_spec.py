from typing import ClassVar

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectPrefillHandler,
    BaseObjectSpec,
)


class GebiedsaanwijzingMixin(BaseModel):
    __object_type__: ClassVar[str] = "gebiedsaanwijzing"
    __inheritable__: ClassVar[set[str]] = {"title", "ref_type", "ref_group", "target_codes"}
    __object_fields__: ClassVar[set[str]] = {"title", "ref_type", "ref_group", "target_codes"}

    title: str | None = None
    ref_type: str | None = None
    ref_group: str | None = None
    target_codes: list[str] | None = None


class GebiedsaanwijzingSpec(GebiedsaanwijzingMixin, BaseObjectSpec):
    pass


class GebiedsaanwijzingPrefillHandler(BaseObjectPrefillHandler[GebiedsaanwijzingSpec]):
    pass


class GebiedsaanwijzingPersistHandler(BaseObjectPersistHandler[GebiedsaanwijzingSpec]):
    pass
