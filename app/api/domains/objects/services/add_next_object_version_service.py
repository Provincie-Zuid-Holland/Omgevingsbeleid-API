import uuid

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.domains.objects.types import NextObjectVersion
from app.core.tables.objects import ObjectsTable


class AddNextObjectVersionConfig(BaseModel):
    to_field: str
    object_uuids: list[uuid.UUID]


class AddNextObjectVersionService:
    def __init__(
        self,
        session: Session,
        config: AddNextObjectVersionConfig,
        rows: list[BaseModel],
    ):
        self._session: Session = session
        self._config: AddNextObjectVersionConfig = config
        self._rows: list[BaseModel] = rows

    def add_next_versions(self) -> list[BaseModel]:
        next_version_map: dict[uuid.UUID, NextObjectVersion] = self._fetch()

        for row in self._rows:
            object_id: uuid.UUID = row.id
            if object_id in next_version_map:
                setattr(row, self._config.to_field, next_version_map[object_id])

        return self._rows

    def _fetch(self) -> dict[uuid.UUID, NextObjectVersion]:
        # acts as context to match new versions against
        reference_subq = (
            select(
                ObjectsTable.id.label("previous_id"),
                ObjectsTable.code.label("ref_code"),
                ObjectsTable.modified_date.label("ref_modified_date"),
            ).where(ObjectsTable.id.in_(self._config.object_uuids))
        ).subquery("input_object_reference")

        row_number_col = (
            func.row_number()
            .over(partition_by=reference_subq.c.previous_id, order_by=ObjectsTable.modified_date.asc())
            .label("_row_number")
        )

        # the actual query matching the input rows CTE -> next versions
        next_obj_subq = (
            select(
                reference_subq.c.previous_id,
                row_number_col,
                ObjectsTable.id,
                ObjectsTable.title,
                ObjectsTable.start_validity,
                ObjectsTable.end_validity,
                ObjectsTable.created_date,
                ObjectsTable.modified_date,
            )
            .join(
                ObjectsTable,
                (ObjectsTable.code == reference_subq.c.ref_code)
                & (ObjectsTable.modified_date > reference_subq.c.ref_modified_date),
            )
            .subquery("next_object_versions_view")
        )

        stmt = select(next_obj_subq).where(next_obj_subq.c._row_number == 1)

        db_result = self._session.execute(stmt).all()
        next_version_map: dict[uuid.UUID, NextObjectVersion] = {}
        for db_row in db_result:
            next_version: NextObjectVersion = NextObjectVersion.model_validate(db_row)
            next_version_map[next_version.previous_id] = next_version

        return next_version_map


class AddNextObjectVersionServiceFactory:
    def create_service(
        self,
        session: Session,
        config: AddNextObjectVersionConfig,
        rows: list[BaseModel],
    ) -> AddNextObjectVersionService:
        return AddNextObjectVersionService(
            session=session,
            config=config,
            rows=rows,
        )
