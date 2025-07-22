from typing import Dict, List, Set, Type, get_args

from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.core.tables.objects import ObjectsTable
from app.core.types import Model


class JoinOnderverdelingenConfig(BaseModel):
    onderverdelingen_codes: Set[str]
    response_model: Model  # Of the row, not the Onderverdeling that we are about to join
    from_field: str
    to_field: str


class JoinOnderverdelingenService:
    def __init__(
        self,
        object_repository: ObjectRepository,
        session: Session,
        config: JoinOnderverdelingenConfig,
    ):
        self._object_repository: ObjectRepository = object_repository
        self._session: Session = session
        self._config: JoinOnderverdelingenConfig = config

    def join_onderverdelingen(self, rows: List[BaseModel]) -> List[BaseModel]:
        if len(self._config.onderverdelingen_codes) == 0:
            return rows

        onderverdelingen: Dict[str, BaseModel] = self._fetch_onderverdelingen()

        result_rows: List[BaseModel] = []
        for row in rows:
            requested_codes: List[str] = getattr(row, self._config.from_field)

            result_for_row: List[BaseModel] = []
            for onderverdeling_code in requested_codes:
                onderverdeling = onderverdelingen.get(onderverdeling_code)
                if not onderverdeling:
                    continue
                result_for_row.append(onderverdeling)

            setattr(row, self._config.to_field, result_for_row)
            result_rows.append(row)

        return result_rows

    def _fetch_onderverdelingen(self) -> Dict[str, BaseModel]:
        onderverdeling_annotation = self._config.response_model.pydantic_model.__annotations__.get(
            self._config.to_field
        )
        onderverdeling_model: Type[BaseModel] = get_args(onderverdeling_annotation)[0]

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
                ObjectsTable.Code.in_(self._config.onderverdelingen_codes),
            )
            .subquery()
        )

        stmt = select(subq).filter(subq.c._RowNumber == 1)

        rows = self._session.execute(stmt).all()
        result: Dict[str, BaseModel] = {r.Code: onderverdeling_model.model_validate(r) for r in rows}

        return result


class JoinOnderverdelingenServiceFactory:
    def __init__(self, object_repository: ObjectRepository):
        self._object_repository: ObjectRepository = object_repository

    def create_service(
        self,
        session: Session,
        config: JoinOnderverdelingenConfig,
    ) -> JoinOnderverdelingenService:
        return JoinOnderverdelingenService(
            self._object_repository,
            session,
            config,
        )
