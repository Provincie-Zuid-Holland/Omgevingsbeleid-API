from typing import Optional
from uuid import UUID

from sqlalchemy import desc, select

from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.repository import BaseRepository


class ObjectRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[ObjectsTable]:
        stmt = select(ObjectsTable).filter(ObjectsTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_by_object_type_and_uuid(
        self, object_type: str, uuid: UUID
    ) -> Optional[ObjectsTable]:
        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.UUID == uuid)
            .filter(ObjectsTable.Object_Type == object_type)
        )
        return self.fetch_first(stmt)

    def get_latest_by_id(
        self, object_type: str, object_id: int
    ) -> Optional[ObjectsTable]:
        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.Object_Type == object_type)
            .filter(ObjectsTable.Object_ID == object_id)
            .order_by(desc(ObjectsTable.Modified_Date))
        )
        return self.fetch_first(stmt)
