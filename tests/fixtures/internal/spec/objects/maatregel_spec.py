from typing import ClassVar

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectPrefillHandler,
    BaseObjectSpec,
)


class MaatregelMixin(BaseModel):
    __object_type__: ClassVar[str] = "maatregel"
    __inheritable__: ClassVar[set[str]] = {
        "title",
        "description",
        "effect",
        "hierarchy_code",
        "gebiedengroep_code",
        "roles",
    }
    __object_fields__: ClassVar[set[str]] = {
        "title",
        "description",
        "effect",
        "hierarchy_code",
        "gebiedengroep_code",
        "roles",
    }

    title: str | None = None
    description: str | None = None
    effect: str | None = None
    hierarchy_code: str | None = None
    gebiedengroep_code: str | None = None
    roles: list[str] | None = None


class MaatregelSpec(MaatregelMixin, BaseObjectSpec):
    pass


class MaatregelPrefillHandler(BaseObjectPrefillHandler[MaatregelSpec]):
    pass


class MaatregelPersistHandler(BaseObjectPersistHandler[MaatregelSpec]):
    pass
