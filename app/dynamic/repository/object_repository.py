from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Query, Session, aliased
from sqlalchemy.sql import func

from app.dynamic.db.objects_table import ObjectsTable


class ObjectRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_uuid(self, uuid: UUID) -> Optional[ObjectsTable]:
        stmt = select(ObjectsTable).filter(ObjectsTable.UUID == uuid)
        maybe_object = self._db.scalars(stmt).first()
        return maybe_object

    def get_by_object_type_and_uuid(
        self, object_type: str, uuid: UUID
    ) -> Optional[ObjectsTable]:
        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.UUID == uuid)
            .filter(ObjectsTable.Object_Type == object_type)
        )
        maybe_object = self._db.scalars(stmt).first()
        return maybe_object

    def get_latest_by_id(
        self, object_type: str, object_id: int
    ) -> Optional[ObjectsTable]:
        stmt = (
            select(ObjectsTable)
            .filter(ObjectsTable.Object_Type == object_type)
            .filter(ObjectsTable.Object_ID == object_id)
            .order_by(desc(ObjectsTable.Modified_Date))
        )
        return self._db.scalars(stmt).first()

    @staticmethod
    def all_latest_query(in_area: Optional[List[UUID]]):
        """
        Builds a base query selecting all objects with the last modified
        version per Code.
        """
        subq = select(
            ObjectsTable,
            func.row_number()
            .over(
                partition_by=ObjectsTable.Code,
                order_by=desc(ObjectsTable.Modified_Date),
            )
            .label("_RowNumber"),
        ).select_from(ObjectsTable)

        if in_area:
            subq = subq.filter(ObjectsTable.Gebied_UUID.in_(in_area))

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c.get("_RowNumber") == 1)
            .order_by(desc(subq.c.Modified_Date))
        )
        return stmt

    def get_all_latest(self) -> List[ObjectsTable]:
        """
        Execute a fetch of all latest valid objects.
        """
        query = self.all_latest_query()
        return self._db.scalars(query).all()

    def get_latest_in_area(self, in_area: Optional[List[UUID]]) -> List[ObjectsTable]:
        """
        Find all latest objects matching a list of Werkingsgebied UUIDs
        """
        query = self.all_latest_query(in_area=in_area)
        return self._db.scalars(query).all()
