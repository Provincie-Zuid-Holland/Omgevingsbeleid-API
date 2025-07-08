import uuid
from typing import Dict, List

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.domains.objects.types import NextObjectVersion
from app.core.tables.objects import ObjectsTable


class AddNextObjectVersionConfig(BaseModel):
    to_field: str
    object_uuids: List[uuid.UUID]


class AddNextObjectVersionService:
    def __init__(
        self,
        db: Session,
        config: AddNextObjectVersionConfig,
        rows: List[BaseModel],
    ):
        self._db: Session = db
        self._config: AddNextObjectVersionConfig = config
        self._rows: List[BaseModel] = rows

    def add_next_versions(self) -> List[BaseModel]:
        next_version_map: Dict[uuid.UUID, NextObjectVersion] = self._fetch()

        for row in self._rows:
            object_uuid: uuid.UUID = getattr(row, "UUID")
            if object_uuid in next_version_map:
                setattr(row, self._config.to_field, next_version_map[object_uuid])

        return self._rows

    def _fetch(self) -> Dict[uuid.UUID, NextObjectVersion]:
        # acts as context to match new versions against
        reference_subq = (
            select(
                ObjectsTable.UUID.label("Previous_UUID"),
                ObjectsTable.Code.label("ref_code"),
                ObjectsTable.Modified_Date.label("ref_modified_date"),
            ).where(ObjectsTable.UUID.in_(self._config.object_uuids))
        ).subquery("input_object_reference")

        row_number_col = (
            func.row_number()
            .over(partition_by=reference_subq.c.Previous_UUID, order_by=ObjectsTable.Modified_Date.asc())
            .label("_RowNumber")
        )

        # the actual query matching the input rows CTE -> next versions
        next_obj_subq = (
            select(
                reference_subq.c.Previous_UUID,
                row_number_col,
                ObjectsTable.UUID,
                ObjectsTable.Title,
                ObjectsTable.Start_Validity,
                ObjectsTable.End_Validity,
                ObjectsTable.Created_Date,
                ObjectsTable.Modified_Date,
            )
            .join(
                ObjectsTable,
                (ObjectsTable.Code == reference_subq.c.ref_code)
                & (ObjectsTable.Modified_Date > reference_subq.c.ref_modified_date),
            )
            .subquery("next_object_versions_view")
        )

        stmt = select(next_obj_subq).where(next_obj_subq.c._RowNumber == 1)

        db_result = self._db.execute(stmt).all()
        next_version_map: Dict[uuid.UUID, NextObjectVersion] = {}
        for db_row in db_result:
            next_version: NextObjectVersion = NextObjectVersion.model_validate(db_row)
            next_version_map[next_version.Previous_UUID] = next_version

        return next_version_map


class AddNextObjectVersionServiceFactory:
    def __init__(self, db: Session):
        self._db: Session = db

    def create_service(
        self,
        config: AddNextObjectVersionConfig,
        rows: List[BaseModel],
    ) -> AddNextObjectVersionService:
        return AddNextObjectVersionService(
            db=self._db,
            config=config,
            rows=rows,
        )
