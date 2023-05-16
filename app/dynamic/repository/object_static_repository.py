from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.orm import Session, Query

from app.dynamic.db import ObjectStaticsTable


class ObjectStaticRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_object_type_and_id(
        self, object_type: str, object_id: int
    ) -> Optional[ObjectStaticsTable]:
        stmt = (
            select(ObjectStaticsTable)
            .filter(ObjectStaticsTable.Object_Type == object_type)
            .filter(ObjectStaticsTable.Object_ID == object_id)
        )
        maybe_object = self._db.scalars(stmt).first()
        return maybe_object

    def get_by_type_and_owner(
        self, object_type: str = None, owner_uuid: UUID = None
    ) -> List[ObjectStaticsTable]:
        query = Query(ObjectStaticsTable)

        if owner_uuid:
            type_filter = or_(
                ObjectStaticsTable.Owner_1_UUID == owner_uuid,
                ObjectStaticsTable.Owner_2_UUID == owner_uuid,
            )
            query = query.filter(type_filter)

        if object_type:
            query = query.filter(ObjectStaticsTable.Object_Type == object_type)

        query.session = self._db
        return query.all()
