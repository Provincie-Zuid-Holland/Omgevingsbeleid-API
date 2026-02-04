from typing import Dict, List, Set

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.objects.types import ObjectStatics
from app.core.tables.objects import ObjectStaticsTable


class JoinGebiedenConfig(BaseModel):
    gebieden_codes: Set[str]
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
        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.Code.in_(self._config.gebieden_codes))
        rows = self._session.execute(stmt).scalars().all()

        return {r.Code: ObjectStatics.model_validate(r) for r in rows}


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
