from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.extensions.modules.db.tables import ModuleObjectContextTable


class ModuleObjectContextRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_by_ids(self, module_id: int, object_type: str, object_id: int) -> Optional[ModuleObjectContextTable]:
        stmt = (
            select(ModuleObjectContextTable)
            .filter(ModuleObjectContextTable.Object_Type == object_type)
            .filter(ModuleObjectContextTable.Object_ID == object_id)
            .filter(ModuleObjectContextTable.Module_ID == module_id)
        )

        maybe_context = self._db.scalars(stmt).first()
        return maybe_context
