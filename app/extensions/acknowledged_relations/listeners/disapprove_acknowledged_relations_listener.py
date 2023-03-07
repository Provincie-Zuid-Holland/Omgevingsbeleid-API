from typing import List
from sqlalchemy import or_, update
from sqlalchemy.orm import Session

from app.dynamic.event.types import Listener
from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.modules.event.module_status_changed_event import (
    ModuleStatusChangedEvent,
)
from app.extensions.modules.models.models import ModuleSnapshot


class DisapproveAcknowledgedRelationsListener(Listener[ModuleStatusChangedEvent]):
    def handle_event(self, event: ModuleStatusChangedEvent) -> ModuleStatusChangedEvent:
        if event.context.new_status.Status != "Vigerend gearchiveerd":
            return

        snapshot: ModuleSnapshot = event.get_snapshot()
        objects: List[dict] = snapshot.Objects
        codes: List[str] = list(set([o.get("Code") for o in objects]))
        if not codes:
            return

        stmt = (
            update(AcknowledgedRelationsTable)
            .filter(
                or_(
                    AcknowledgedRelationsTable.From_Code.in_(codes),
                    AcknowledgedRelationsTable.To_Code.in_(codes),
                )
            )
            .values(
                From_Acknowledged=False,
                To_Acknowledged=False,
            )
        )
        db: Session = event.get_db()
        db.execute(stmt)
        db.commit()
