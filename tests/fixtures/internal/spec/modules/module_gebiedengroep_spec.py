from typing import ClassVar

from tests.fixtures.internal.spec.modules.base_module_object_spec import (
    BaseModuleObjectPersistHandler,
    BaseModuleObjectPrefillHandler,
    BaseModuleObjectSpec,
)
from tests.fixtures.internal.spec.objects.base_object_spec import BaseObjectSpec
from tests.fixtures.internal.spec.objects.gebiedengroep_spec import GebiedengroepMixin, GebiedengroepSpec


class ModuleGebiedengroepSpec(GebiedengroepMixin, BaseModuleObjectSpec):
    __vigerend_spec__: ClassVar[type[BaseObjectSpec]] = GebiedengroepSpec


class ModuleGebiedengroepPrefillHandler(BaseModuleObjectPrefillHandler[ModuleGebiedengroepSpec]):
    pass


class ModuleGebiedengroepPersistHandler(BaseModuleObjectPersistHandler[ModuleGebiedengroepSpec]):
    pass
