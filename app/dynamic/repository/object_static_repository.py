from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_, select

from app.dynamic.db import ObjectStaticsTable
from app.dynamic.repository.repository import BaseRepository


class ObjectStaticRepository(BaseRepository):
    def get_by_object_type_and_id(self, object_type: str, object_id: int) -> Optional[ObjectStaticsTable]:
        stmt = (
            select(ObjectStaticsTable)
            .filter(ObjectStaticsTable.Object_Type == object_type)
            .filter(ObjectStaticsTable.Object_ID == object_id)
        )
        return self.fetch_first(stmt)

    def get_by_type_and_owner(
        self, object_type: Optional[str] = None, owner_uuid: Optional[UUID] = None
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

        return self.fetch_all(stmt)
