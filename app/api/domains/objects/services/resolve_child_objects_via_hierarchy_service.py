import uuid
from collections import defaultdict
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.tables.objects import ObjectsTable
from app.core.types import Model


class ResolveChildObjectsViaHierarchyConfig(BaseModel):
    to_field: str
    response_model: Model


class HierachyReference(BaseModel):
    id: uuid.UUID
    object_type: str
    object_id: int
    code: str
    hierarchy_code: str
    title: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ResolveChildObjectsViaHierarchyService:
    def __init__(
        self,
        session: Session,
        config: ResolveChildObjectsViaHierarchyConfig,
    ):
        self._session: Session = session
        self._config: ResolveChildObjectsViaHierarchyConfig = config

    def resolve_child_objects(self, rows: list[BaseModel]) -> list[BaseModel]:
        target_codes: set[str] = {row.code for row in rows}
        child_rows = self._fetch_children(target_codes)

        map_for_target: dict[str, list[HierachyReference]] = defaultdict(list)
        for child_row in child_rows:
            map_for_target[child_row.hierarchy_code].append(child_row)

        for row in rows:
            children: list[HierachyReference] = map_for_target.get(row.code, [])
            setattr(row, self._config.to_field, children)

        return rows

    def _fetch_children(self, hierarchy_targets: set[str]) -> list[HierachyReference]:
        if len(hierarchy_targets) == 0:
            return []

        subq = (
            select(
                ObjectsTable.id,
                ObjectsTable.object_type,
                ObjectsTable.object_id,
                ObjectsTable.code,
                ObjectsTable.hierarchy_code,
                ObjectsTable.title,
                ObjectsTable.end_validity,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.code,
                    order_by=desc(ObjectsTable.modified_date),
                )
                .label("_row_number"),
            )
            .filter(ObjectsTable.start_validity <= datetime.now(UTC))
            .subquery()
        )

        stmt = (
            select(subq)
            .filter(subq.c._row_number == 1)
            .filter(subq.c.hierarchy_code.in_(hierarchy_targets))
            .filter(
                or_(
                    subq.c.end_validity > datetime.now(UTC),
                    subq.c.end_validity.is_(None),
                )
            )
        )

        child_rows = self._session.execute(stmt).all()

        result: list[HierachyReference] = [HierachyReference.model_validate(child) for child in child_rows]

        return result


class ResolveChildObjectsViaHierarchyServiceFactory:
    def create_service(
        self,
        session: Session,
        config: ResolveChildObjectsViaHierarchyConfig,
    ):
        return ResolveChildObjectsViaHierarchyService(
            session=session,
            config=config,
        )
