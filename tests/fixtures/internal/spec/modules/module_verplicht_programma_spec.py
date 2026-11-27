from typing import ClassVar

from tests.fixtures.internal.spec.modules.base_module_object_spec import (
    BaseModuleObjectPersistHandler,
    BaseModuleObjectPrefillHandler,
    BaseModuleObjectSpec,
)
from tests.fixtures.internal.spec.objects.base_object_spec import BaseObjectSpec
from tests.fixtures.internal.spec.objects.maatregel_spec import MaatregelMixin, MaatregelSpec


class ModuleVerplichtProgrammaSpec(MaatregelMixin, BaseModuleObjectSpec):
    __vigerend_spec__: ClassVar[type[BaseObjectSpec]] = MaatregelSpec


class ModuleVerplichtProgrammaPrefillHandler(BaseModuleObjectPrefillHandler[ModuleVerplichtProgrammaSpec]):
    pass


class ModuleVerplichtProgrammaPersistHandler(BaseModuleObjectPersistHandler[ModuleVerplichtProgrammaSpec]):
    pass
