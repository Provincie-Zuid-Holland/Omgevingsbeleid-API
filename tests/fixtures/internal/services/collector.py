
from datetime import datetime
from typing import Any, Dict, List, Optional, Type


from tests.fixtures.internal.types import Spec, Ref, Record, FixtureCtx
from tests.fixtures.internal.services.contexts import DefaultsCtx, ModuleCtx



class Collector:
    def __init__(self) -> None:
        self._records: List[Record] = []

        # Context services
        self._defaults: Dict[str, Any] = {}
        self._current_module_id: Optional[int] = 0

    def at(self, timepoint: datetime) -> None:
        self.set_defaults(
            Created_Date=timepoint,
            Modified_Date=timepoint,
        )
    
    def adds(self, specs: List[Spec]) -> None:
        for spec in specs:
            self.add(spec)

    def add(self, spec: Spec) -> None:
        # @todo: fill with defaults etc

        self._records.append(Record(
            spec=spec,
            spec_type=type(spec),
            ctx=FixtureCtx(
                module=self._current_module_id,
                defaults=self._defaults,
            )
        ))

    # For ModuleCtx

    def in_module(self, module_id: int) -> ModuleCtx:
        return ModuleCtx(self, module_id)

    # For DefaultsCtx

    def set_defaults(self, **kwargs: Any) -> None:
        self._defaults.update(kwargs)
    
    def with_defaults(self, **kwargs: Any) -> DefaultsCtx:
        return DefaultsCtx(self, kwargs)
    
    # Helpers
    def ref(self, spec_type: Type[Spec], key: str) -> Ref:
        return Ref(spec_type, key)

    def get_results(self) -> List[Record]:
        return self._records
