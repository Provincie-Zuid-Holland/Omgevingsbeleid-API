from typing import ClassVar, Optional, Set

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectSpec,
    BaseObjectPrefillHandler,
)


class BeleidsdoelSpec(BaseObjectSpec):
    __object_type__: ClassVar[str] = "ambitie"
    __inheritable__: ClassVar[Set[str]] = {"Title", "Description"}
    __object_fields__: ClassVar[Set[str]] = {"Title", "Description"}

    Title: Optional[str] = None
    Description: Optional[str] = None


class BeleidsdoelPrefillHandler(BaseObjectPrefillHandler[BeleidsdoelSpec]):
    pass


class BeleidsdoelPersistHandler(BaseObjectPersistHandler[BeleidsdoelSpec]):
    pass
