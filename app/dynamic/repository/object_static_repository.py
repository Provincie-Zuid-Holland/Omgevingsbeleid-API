from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

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
