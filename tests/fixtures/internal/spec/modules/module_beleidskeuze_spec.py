from typing import ClassVar, Type

from tests.fixtures.internal.spec.objects.base_object_spec import BaseObjectSpec
from tests.fixtures.internal.spec.modules.base_module_object_spec import (
    BaseModuleObjectSpec,
    BaseModuleObjectPrefillHandler,
    BaseModuleObjectPersistHandler,
)
from tests.fixtures.internal.spec.objects.beleidskeuze_spec import BeleidskeuzeMixin, BeleidskeuzeSpec


class ModuleBeleidskeuzeSpec(BeleidskeuzeMixin, BaseModuleObjectSpec):
    __vigerend_spec__: ClassVar[Type[BaseObjectSpec]] = BeleidskeuzeSpec


class ModuleBeleidskeuzePrefillHandler(BaseModuleObjectPrefillHandler[ModuleBeleidskeuzeSpec]):
    pass


class ModuleBeleidskeuzePersistHandler(BaseModuleObjectPersistHandler[ModuleBeleidskeuzeSpec]):
    pass
