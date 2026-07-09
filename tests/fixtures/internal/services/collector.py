from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Type


from tests.fixtures.internal.types import Spec, Ref, Record, FixtureCtx
from tests.fixtures.internal.services.contexts import DefaultsCtx, ModuleCtx


class Collector:
    def __init__(self) -> None:
        self._records: List[Record] = []

        # Context services
        self._timepoint: datetime = datetime.now(timezone.utc)
        self._defaults: Dict[str, Any] = {}
        self._current_module_id: Optional[int] = 0

        self.at(self._timepoint)

    def adds(self, specs: List[Spec]) -> None:
        for spec in specs:
            self.add(spec)

    def add(self, spec: Spec) -> None:
        self._records.append(
            Record(
                spec=spec,
                ctx=FixtureCtx(
                    module=self._current_module_id,
                    defaults=self._defaults,
                ),
            )
        )

    def update_defaults_for(self, ref: Ref, **kwargs: Any):
        record: Record = self._find(ref)
        record.ctx.defaults.update(kwargs)

    def _find(self, ref: Ref) -> Record:
        for record in self._records:
            if type(record.spec) is not ref.spec_type:
                continue
            if record.spec.key == ref.key:
                return record
        raise RuntimeError("Record with ref {ref!r} not found")

    # For ModuleCtx

    def in_module(self, module_id: int) -> ModuleCtx:
        return ModuleCtx(self, module_id)

    # For DefaultsCtx

    def set_defaults(self, **kwargs: Any) -> None:
        self._apply_defaults(kwargs)

    def with_defaults(self, **kwargs: Any) -> DefaultsCtx:
        return DefaultsCtx(self, kwargs)

    def _apply_defaults(self, data: Dict[str, Any]) -> None:
        # The timepoint and the Created_/Modified_Date defaults are one source of
        # truth: setting the dates here moves the cursor so a following move_at()
        # advances from the explicitly set time, not from a stale timepoint.
        self._defaults.update(data)
        dates = [data[key] for key in ("Created_Date", "Modified_Date") if key in data]
        if dates:
            self._timepoint = max(dates)

    # Time management
    def at(self, timepoint: datetime) -> None:
        self.set_defaults(
            Created_Date=timepoint,
            Modified_Date=timepoint,
        )

    def move_at(self, seconds: float = 0, minutes: float = 0, hours: float = 0, days: float = 0):
        delta: timedelta = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        timepoint: datetime = self._timepoint + delta
        self.at(timepoint)

    def get_timepoint(self) -> datetime:
        return self._timepoint

    # Helpers
    def ref(self, spec_type: Type[Spec], key: str) -> Ref:
        return Ref(spec_type, key)

    def get_results(self) -> List[Record]:
        return self._records
