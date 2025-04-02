from dataclasses import dataclass
from tracemalloc import Snapshot
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core_old.utils.utils import table_to_dict
from app.dynamic.event.types import Event, NoPayload
from app.extensions.modules.db.tables import ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.models.models import ModuleSnapshot
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository


@dataclass
class ModuleStatusChangedEventContext:
    module: ModuleTable
    new_status: ModuleStatusHistoryTable


class ModuleStatusChangedEvent(Event):
    def __init__(
        self,
        payload: NoPayload,
        context: ModuleStatusChangedEventContext,
    ):
        super().__init__()
        self.payload: NoPayload = payload
        self.context: ModuleStatusChangedEventContext = context
        self._snapshot: Optional[Snapshot] = None

    def get_snapshot(self) -> ModuleSnapshot:
        if self._snapshot is not None:
            return self._snapshot

        db: Optional[Session] = self.get_db()
        if db is None:
            raise RuntimeError("Missing db connection")

        repository: ModuleObjectRepository = ModuleObjectRepository(db)
        module_objects: List[dict] = repository.get_objects_in_time(
            self.context.module.Module_ID,
            self.context.new_status.Created_Date,
        )
        dict_objects: List[dict] = [table_to_dict(t) for t in module_objects]
        self._snapshot = ModuleSnapshot(
            Objects=dict_objects,
        )
        return self._snapshot

    @staticmethod
    def create(
        module: ModuleTable,
        new_status: ModuleStatusHistoryTable,
    ):
        return ModuleStatusChangedEvent(
            payload=NoPayload(),
            context=ModuleStatusChangedEventContext(
                module,
                new_status,
            ),
        )
