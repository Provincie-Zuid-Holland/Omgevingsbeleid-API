from typing import ClassVar

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectPrefillHandler,
    BaseObjectSpec,
)


class BeleidsdoelMixin(BaseModel):
    __object_type__: ClassVar[str] = "beleidsdoel"
    __inheritable__: ClassVar[set[str]] = {"Title", "Description"}
    __object_fields__: ClassVar[set[str]] = {"Title", "Description"}

    Title: str | None = None
    Description: str | None = None


class BeleidsdoelSpec(BeleidsdoelMixin, BaseObjectSpec):
    pass


class BeleidsdoelPrefillHandler(BaseObjectPrefillHandler[BeleidsdoelSpec]):
    pass


class BeleidsdoelPersistHandler(BaseObjectPersistHandler[BeleidsdoelSpec]):
    pass
