from typing import ClassVar, Type

from tests.fixtures.internal.spec.objects.base_object_spec import BaseObjectSpec
from tests.fixtures.internal.spec.modules.base_module_object_spec import (
    BaseModuleObjectSpec,
    BaseModuleObjectPrefillHandler,
    BaseModuleObjectPersistHandler,
)
from tests.fixtures.internal.spec.objects.beleidsdoel_spec import BeleidsdoelMixin, BeleidsdoelSpec


class ModuleBeleidsdoelSpec(BeleidsdoelMixin, BaseModuleObjectSpec):
    __vigerend_spec__: ClassVar[Type[BaseObjectSpec]] = BeleidsdoelSpec


class ModuleBeleidsdoelPrefillHandler(BaseModuleObjectPrefillHandler[ModuleBeleidsdoelSpec]):
    pass


class ModuleBeleidsdoelPersistHandler(BaseModuleObjectPersistHandler[ModuleBeleidsdoelSpec]):
    pass
