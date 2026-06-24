from typing import ClassVar, Optional, Set

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectSpec,
    BaseObjectPrefillHandler,
)


class BeleidskeuzeMixin(BaseModel):
    __object_type__: ClassVar[str] = "beleidskeuze"
    __inheritable__: ClassVar[Set[str]] = {
        "Title",
        "Description",
        "Explanation",
        "Hierarchy_Code",
        "Gebiedengroep_Code",
    }
    __object_fields__: ClassVar[Set[str]] = {
        "Title",
        "Description",
        "Explanation",
        "Hierarchy_Code",
        "Gebiedengroep_Code",
    }

    Title: Optional[str] = None
    Description: Optional[str] = None
    Explanation: Optional[str] = None
    Hierarchy_Code: Optional[str] = None
    Gebiedengroep_Code: Optional[str] = None


class BeleidskeuzeSpec(BeleidskeuzeMixin, BaseObjectSpec):
    pass


class BeleidskeuzePrefillHandler(BaseObjectPrefillHandler[BeleidskeuzeSpec]):
    pass


class BeleidskeuzePersistHandler(BaseObjectPersistHandler[BeleidskeuzeSpec]):
    pass
