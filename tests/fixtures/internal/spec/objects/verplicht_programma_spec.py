from typing import ClassVar

from pydantic import BaseModel

from tests.fixtures.internal.spec.objects.base_object_spec import (
    BaseObjectPersistHandler,
    BaseObjectPrefillHandler,
    BaseObjectSpec,
)


class VerplichtProgrammaMixin(BaseModel):
    __object_type__: ClassVar[str] = "verplicht_programma"
    __inheritable__: ClassVar[set[str]] = {"title", "description"}
    __object_fields__: ClassVar[set[str]] = {"title", "description"}

    title: str | None = None
    description: str | None = None


class VerplichtProgrammaSpec(VerplichtProgrammaMixin, BaseObjectSpec):
    pass


class VerplichtProgrammaPrefillHandler(BaseObjectPrefillHandler[VerplichtProgrammaSpec]):
    pass


class VerplichtProgrammaPersistHandler(BaseObjectPersistHandler[VerplichtProgrammaSpec]):
    pass
