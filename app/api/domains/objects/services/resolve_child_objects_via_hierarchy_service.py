from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
import uuid

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func, desc, or_
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
    Title: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ResolveChildObjectsViaHierarchyService:
    def __init__(
        self,
        session: Session,
        config: ResolveChildObjectsViaHierarchyConfig,
    ):
        self._session: Session = session
        self._config: ResolveChildObjectsViaHierarchyConfig = config

    def resolve_child_objects(self, rows: List[BaseModel]) -> List[BaseModel]:
        target_codes: Set[str] = {row.Code for row in rows}
        child_rows = self._fetch_children(target_codes)

        map_for_target: Dict[str, List[HierachyReference]] = defaultdict(list)
        for child_row in child_rows:
            map_for_target[child_row.Hierarchy_Code].append(child_row)

        for row in rows:
            children: List[HierachyReference] = map_for_target.get(row.Code, [])
            setattr(row, self._config.to_field, children)

        return rows

    def _fetch_children(self, hierarchy_targets: Set[str]) -> List[HierachyReference]:
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
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
            .subquery()
        )

        stmt = (
            select(subq)
            .filter(subq.c._RowNumber == 1)
            .filter(subq.c.Hierarchy_Code.in_(hierarchy_targets))
            .filter(
                or_(
                    subq.c.End_Validity > datetime.now(timezone.utc),
                    subq.c.End_Validity.is_(None),
                )
            )
        )

        child_rows = self._session.execute(stmt).all()

        result: List[HierachyReference] = [HierachyReference.model_validate(child) for child in child_rows]

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
