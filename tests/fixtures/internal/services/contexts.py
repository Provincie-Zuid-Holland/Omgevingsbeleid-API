from typing import Any, Dict, Optional, Self


from tests.fixtures.internal.types import HasCurrentModule, HasDefaults


class DefaultsCtx:
    def __init__(self, target: HasDefaults, data: Dict[str, Any]) -> None:
        self._target: HasDefaults = target
        self._data: Dict[str, Any] = data
        self._previous_data: Dict[str, Any] = {}

    def __enter__(self) -> Self:
        self._previous_data = dict(self._target._defaults)
        self._target._defaults.update(self._data)
        return self

    def __exit__(self, *_: Any) -> None:
        self._target._defaults = self._previous_data


class ModuleCtx:
    def __init__(self, target: HasCurrentModule, module_id: int) -> None:
        self._target: HasCurrentModule = target
        self._module_id: int = module_id
        self._previous: Optional[int] = None

    def __enter__(self) -> Self:
        self._previous = self._target._current_module_id
        self._target._current_module_id = self._module_id
        return self

    def __exit__(self, *_: Any) -> None:
        self._target._current_module_id = self._previous
