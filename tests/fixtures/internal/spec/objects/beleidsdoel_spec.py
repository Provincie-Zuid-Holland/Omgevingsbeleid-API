from typing import ClassVar, Optional, Set

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectSpec,
    BaseObjectPrefillHandler,
)


class BeleidsdoelMixin(BaseModel):
    __object_type__: ClassVar[str] = "beleidsdoel"
    __inheritable__: ClassVar[Set[str]] = {"Title", "Description"}
    __object_fields__: ClassVar[Set[str]] = {"Title", "Description"}

    Title: Optional[str] = None
    Description: Optional[str] = None


class BeleidsdoelSpec(BeleidsdoelMixin, BaseObjectSpec):
    pass


class BeleidsdoelPrefillHandler(BaseObjectPrefillHandler[BeleidsdoelSpec]):
    pass


class BeleidsdoelPersistHandler(BaseObjectPersistHandler[BeleidsdoelSpec]):
    pass
