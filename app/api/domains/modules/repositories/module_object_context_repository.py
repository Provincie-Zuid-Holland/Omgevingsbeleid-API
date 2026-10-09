from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.modules import ModuleObjectContextTable


class ModuleObjectContextRepository(BaseRepository):
    def get_by_ids(
        self, session: Session, module_id: int, object_type: str, object_id: int
    ) -> ModuleObjectContextTable | None:
        stmt = (
            select(ModuleObjectContextTable)
            .filter(ModuleObjectContextTable.object_type == object_type)
            .filter(ModuleObjectContextTable.object_id == object_id)
            .filter(ModuleObjectContextTable.module_id == module_id)
        )

        maybe_context: ModuleObjectContextTable | None = session.scalars(stmt).first()
        return maybe_context
