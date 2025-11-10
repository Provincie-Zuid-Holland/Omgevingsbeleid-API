from typing import Dict, List, Set, Type, get_args

from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.core.tables.objects import ObjectsTable
from app.core.types import Model


class JoinGebiedenConfig(BaseModel):
    gebieden_codes: Set[str]
    response_model: Model  # Of the row, not the Gebied that we are about to join
    from_field: str
    to_field: str


class JoinGebiedenService:
    def __init__(
        self,
        object_repository: ObjectRepository,
        session: Session,
        config: JoinGebiedenConfig,
    ):
        self._object_repository: ObjectRepository = object_repository
        self._session: Session = session
        self._config: JoinGebiedenConfig = config

    def join_gebieden(self, rows: List[BaseModel]) -> List[BaseModel]:
        if len(self._config.gebieden_codes) == 0:
            return rows

        gebieden: Dict[str, BaseModel] = self._fetch_gebieden()

        result_rows: List[BaseModel] = []
        for row in rows:
            requested_codes: List[str] = getattr(row, self._config.from_field)

            result_for_row: List[BaseModel] = []
            for gebieden_code in requested_codes:
                gebied = gebieden.get(gebieden_code)
                if not gebied:
                    continue
                result_for_row.append(gebied)

            setattr(row, self._config.to_field, result_for_row)
            result_rows.append(row)

        return result_rows

    def _fetch_gebieden(self) -> Dict[str, BaseModel]:
        gebied_annotation = self._config.response_model.pydantic_model.__annotations__.get(self._config.to_field)
        gebied_model: Type[BaseModel] = get_args(gebied_annotation)[0]

        subq = (
            select(
                ObjectsTable,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.Code,
                    order_by=desc(ObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ObjectsTable)
            .filter(
                ObjectsTable.Code.in_(self._config.gebieden_codes),
            )
            .subquery()
        )

        stmt = select(subq).filter(subq.c._RowNumber == 1)

        rows = self._session.execute(stmt).all()
        result: Dict[str, BaseModel] = {r.Code: gebied_model.model_validate(r) for r in rows}

        return result


class JoinGebiedenServiceFactory:
    def __init__(self, object_repository: ObjectRepository):
        self._object_repository: ObjectRepository = object_repository

    def create_service(
        self,
        session: Session,
        config: JoinGebiedenConfig,
    ) -> JoinGebiedenService:
        return JoinGebiedenService(
            self._object_repository,
            session,
            config,
        )
