from typing import ClassVar

from tests.fixtures.internal.spec.modules.base_module_object_spec import (
    BaseModuleObjectPersistHandler,
    BaseModuleObjectPrefillHandler,
    BaseModuleObjectSpec,
)
from tests.fixtures.internal.spec.objects.base_object_spec import BaseObjectSpec
from tests.fixtures.internal.spec.objects.gebiedsaanwijzing_spec import GebiedsaanwijzingMixin, GebiedsaanwijzingSpec


class ModuleGebiedsaanwijzingSpec(GebiedsaanwijzingMixin, BaseModuleObjectSpec):
    __vigerend_spec__: ClassVar[type[BaseObjectSpec]] = GebiedsaanwijzingSpec


class ModuleGebiedsaanwijzingPrefillHandler(BaseModuleObjectPrefillHandler[ModuleGebiedsaanwijzingSpec]):
    pass


class ModuleGebiedsaanwijzingPersistHandler(BaseModuleObjectPersistHandler[ModuleGebiedsaanwijzingSpec]):
    pass
