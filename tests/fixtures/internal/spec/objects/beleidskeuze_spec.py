from typing import ClassVar

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectPrefillHandler,
    BaseObjectSpec,
)


class BeleidskeuzeMixin(BaseModel):
    __object_type__: ClassVar[str] = "beleidskeuze"
    __inheritable__: ClassVar[set[str]] = {
        "title",
        "description",
        "explanation",
        "hierarchy_code",
        "gebiedengroep_code",
    }
    __object_fields__: ClassVar[set[str]] = {
        "title",
        "description",
        "explanation",
        "hierarchy_code",
        "gebiedengroep_code",
    }

    title: str | None = None
    description: str | None = None
    explanation: str | None = None
    hierarchy_code: str | None = None
    gebiedengroep_code: str | None = None


class BeleidskeuzeSpec(BeleidskeuzeMixin, BaseObjectSpec):
    pass


class BeleidskeuzePrefillHandler(BaseObjectPrefillHandler[BeleidskeuzeSpec]):
    pass


class BeleidskeuzePersistHandler(BaseObjectPersistHandler[BeleidskeuzeSpec]):
    pass
