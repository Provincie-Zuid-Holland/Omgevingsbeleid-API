from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from app.core.services.event.types import Event
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.users import UsersTable
from app.core.types import Model


@dataclass
class ModuleObjectPatchedEventContext:
    user: UsersTable
    changes: Dict[str, str]
    timepoint: datetime
    request_model: Model
    old_record: ModuleObjectsTable


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
        old_record: ModuleObjectsTable,
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
                old_record=old_record,
            ),
        )
