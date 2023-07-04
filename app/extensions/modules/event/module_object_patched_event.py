from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from app.dynamic.config.models import Model
from app.dynamic.event.types import Event
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.users.db.tables import UsersTable


@dataclass
class ModuleObjectPatchedEventContext:
    user: UsersTable
    changes: Dict[str, str]
    timepoint: datetime
    request_model: Model


@dataclass
class ModuleObjectPatchedEventPayload:
    new_record: ModuleObjectsTable


class ModuleObjectPatchedEvent(Event):
    def __init__(
        self,
        payload: ModuleObjectPatchedEventPayload,
        context: ModuleObjectPatchedEventContext,
    ):
        super().__init__()
        self.payload: ModuleObjectPatchedEventPayload = payload
        self.context: ModuleObjectPatchedEventContext = context

    @staticmethod
    def create(
        user: UsersTable,
        changes: Dict[str, str],
        timepoint: datetime,
        request_model: Model,
        new_record: ModuleObjectsTable,
    ):
        return ModuleObjectPatchedEvent(
            payload=ModuleObjectPatchedEventPayload(
                new_record=new_record,
            ),
            context=ModuleObjectPatchedEventContext(
                user=user,
                changes=changes,
                timepoint=timepoint,
                request_model=request_model,
            ),
        )
