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
        "Title",
        "Description",
        "Explanation",
        "Hierarchy_Code",
        "Gebiedengroep_Code",
    }
    __object_fields__: ClassVar[set[str]] = {
        "Title",
        "Description",
        "Explanation",
        "Hierarchy_Code",
        "Gebiedengroep_Code",
    }

    Title: str | None = None
    Description: str | None = None
    Explanation: str | None = None
    Hierarchy_Code: str | None = None
    Gebiedengroep_Code: str | None = None


class BeleidskeuzeSpec(BeleidskeuzeMixin, BaseObjectSpec):
    pass


class BeleidskeuzePrefillHandler(BaseObjectPrefillHandler[BeleidskeuzeSpec]):
    pass


class BeleidskeuzePersistHandler(BaseObjectPersistHandler[BeleidskeuzeSpec]):
    pass
