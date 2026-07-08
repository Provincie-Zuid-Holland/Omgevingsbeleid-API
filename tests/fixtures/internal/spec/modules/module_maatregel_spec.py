from typing import ClassVar, Type

from tests.fixtures.internal.spec.objects.base_object_spec import BaseObjectSpec
from tests.fixtures.internal.spec.modules.base_module_object_spec import (
    BaseModuleObjectSpec,
    BaseModuleObjectPrefillHandler,
    BaseModuleObjectPersistHandler,
)
from tests.fixtures.internal.spec.objects.maatregel_spec import MaatregelMixin, MaatregelSpec


class ModuleMaatregelSpec(MaatregelMixin, BaseModuleObjectSpec):
    __vigerend_spec__: ClassVar[Type[BaseObjectSpec]] = MaatregelSpec


class ModuleMaatregelPrefillHandler(BaseModuleObjectPrefillHandler[ModuleMaatregelSpec]):
    pass


class ModuleMaatregelPersistHandler(BaseModuleObjectPersistHandler[ModuleMaatregelSpec]):
    pass
