from typing import ClassVar

from tests.fixtures.internal.spec.modules.base_module_object_spec import (
    BaseModuleObjectPersistHandler,
    BaseModuleObjectPrefillHandler,
    BaseModuleObjectSpec,
)
from tests.fixtures.internal.spec.objects.base_object_spec import BaseObjectSpec
from tests.fixtures.internal.spec.objects.gebied_spec import GebiedMixin, GebiedSpec


class ModuleGebiedSpec(GebiedMixin, BaseModuleObjectSpec):
    __vigerend_spec__: ClassVar[type[BaseObjectSpec]] = GebiedSpec


class ModuleGebiedPrefillHandler(BaseModuleObjectPrefillHandler[ModuleGebiedSpec]):
    pass


class ModuleGebiedPersistHandler(BaseModuleObjectPersistHandler[ModuleGebiedSpec]):
    pass
