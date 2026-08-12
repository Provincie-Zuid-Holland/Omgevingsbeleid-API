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
    UUID: uuid.UUID
    Object_Type: str
    Object_ID: int
    Code: str
    Hierarchy_Code: str
    Title: str | None = None
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
        target_codes: set[str] = {row.Code for row in rows}
        child_rows = self._fetch_children(target_codes)

        map_for_target: dict[str, list[HierachyReference]] = defaultdict(list)
        for child_row in child_rows:
            map_for_target[child_row.Hierarchy_Code].append(child_row)

        for row in rows:
            children: list[HierachyReference] = map_for_target.get(row.Code, [])
            setattr(row, self._config.to_field, children)

        return rows

    def _fetch_children(self, hierarchy_targets: set[str]) -> list[HierachyReference]:
        if len(hierarchy_targets) == 0:
            return []

        subq = (
            select(
                ObjectsTable.UUID,
                ObjectsTable.Object_Type,
                ObjectsTable.Object_ID,
                ObjectsTable.Code,
                ObjectsTable.Hierarchy_Code,
                ObjectsTable.Title,
                ObjectsTable.End_Validity,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.Code,
                    order_by=desc(ObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .filter(ObjectsTable.Start_Validity <= datetime.now(UTC))
            .subquery()
        )

        stmt = (
            select(subq)
            .filter(subq.c._RowNumber == 1)
            .filter(subq.c.Hierarchy_Code.in_(hierarchy_targets))
            .filter(
                or_(
                    subq.c.End_Validity > datetime.now(UTC),
                    subq.c.End_Validity.is_(None),
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
