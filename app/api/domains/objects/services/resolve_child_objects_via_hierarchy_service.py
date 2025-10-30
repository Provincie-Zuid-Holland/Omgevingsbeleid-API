from datetime import datetime, timezone
from typing import List, Sequence, Tuple

from pydantic import BaseModel
from sqlalchemy import select, func, desc, or_, Row
from sqlalchemy.orm import Session, aliased

from app.api.domains.modules.types import GenericObjectShort
from app.api.domains.objects.types import ObjectStatics
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable
from app.core.types import Model


class ResolveChildObjectsViaHierarchyConfig(BaseModel):
    to_field: str
    response_model: Model


class ResolveChildObjectsViaHierarchyService:
    def __init__(
        self,
        session: Session,
        rows: List[BaseModel],
        config: ResolveChildObjectsViaHierarchyConfig,
    ):
        self._session: Session = session
        self._rows: List[BaseModel] = rows
        self._config: ResolveChildObjectsViaHierarchyConfig = config

    def resolve_child_objects(self) -> List[BaseModel]:
        result = []
        for row in self._rows:
            child_objects = self._fetch_child_objects(row.Code)  # TODO I don't know about row having a 'Code' field
            result.append(child_objects)

        return result

    def _fetch_child_objects(self, Object_Code: str) -> List[BaseModel]:
        # field_annotation = self._config.response_model.pydantic_model.__annotations__.get(self._config.to_field)
        # field_model: Type[BaseModel] = get_args(field_annotation)[0]

        subq = (
            select(
                ObjectsTable,
                ObjectStaticsTable,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.Code,
                    order_by=desc(ObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
            .filter(ObjectsTable.Hierarchy_Code == Object_Code)
            .subquery()
        )

        aliased_objects = aliased(element=ObjectsTable, alias=subq, name="object_table")
        aliased_object_statics = aliased(element=ObjectStaticsTable, alias=subq, name="object_statics")
        stmt = (
            select(aliased_objects, aliased_object_statics)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.now(timezone.utc),
                    subq.c.End_Validity.is_(None),
                )
            )
        )

        rows: Sequence[Row[Tuple[ObjectsTable, ObjectStatics]]] = self._session.execute(stmt).all()

        result: List[BaseModel] = []
        for row in rows:
            object_table = row.object_table
            object_statics = row.object_statics
            object_short = GenericObjectShort(
                Object_Type=object_statics.Object_Type,
                Object_ID=object_statics.Object_ID,
                UUID=object_table.UUID,
                Title=object_table.Title,
            )
            result.append(object_short)

        return result


class ResolveChildObjectsViaHierarchyServiceFactory:
    def create_service(
        self,
        session: Session,
        rows: List[BaseModel],
        config: ResolveChildObjectsViaHierarchyConfig,
    ):
        return ResolveChildObjectsViaHierarchyService(session=session, rows=rows, config=config)
