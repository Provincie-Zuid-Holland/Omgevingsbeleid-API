from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.objects import ObjectStaticsTable


class ObjectStaticRepository(BaseRepository):
    def get_by_object_type_and_id(
        self, session: Session, object_type: str, object_id: int
    ) -> Optional[ObjectStaticsTable]:
        stmt = (
            select(ObjectStaticsTable)
            .filter(ObjectStaticsTable.Object_Type == object_type)
            .filter(ObjectStaticsTable.Object_ID == object_id)
        )
        return self.fetch_first(session, stmt)

    def get_by_type_and_owner(
        self, session: Session, object_type: Optional[str] = None, owner_uuid: Optional[UUID] = None
    ) -> List[ObjectStaticsTable]:
        stmt = select(ObjectStaticsTable)

        if owner_uuid:
            type_filter = or_(
                ObjectStaticsTable.Owner_1_UUID == owner_uuid,
                ObjectStaticsTable.Owner_2_UUID == owner_uuid,
            )
            stmt = stmt.filter(type_filter)

        if object_type:
            stmt = stmt.filter(ObjectStaticsTable.Object_Type == object_type)

        return self.fetch_all(session, stmt)

    def get_by_source(self, session: Session, source_key: str) -> Optional[ObjectStaticsTable]:
        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.Source_Identifier == source_key)
        return self.fetch_first(session, stmt)
