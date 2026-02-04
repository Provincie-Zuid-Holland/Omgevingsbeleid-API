from typing import Dict, List, Optional, Set

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.objects.types import ObjectStatics
from app.core.tables.objects import ObjectStaticsTable


class JoinGebiedenGroepenConfig(BaseModel):
    gebiedengroepen_codes: Set[str]
    from_field: str
    to_field: str


class JoinGebiedenGroepenService:
    def __init__(
        self,
        object_repository: ObjectRepository,
        session: Session,
        config: JoinGebiedenGroepenConfig,
    ):
        self._object_repository: ObjectRepository = object_repository
        self._session: Session = session
        self._config: JoinGebiedenGroepenConfig = config

    def join_gebiedengroepen(self, rows: List[BaseModel]) -> List[BaseModel]:
        if len(self._config.gebiedengroepen_codes) == 0:
            return rows

        gebiedengroepen: Dict[str, BaseModel] = self._fetch_gebiedengroepen()

        for row in rows:
            requested_code: Optional[str] = getattr(row, self._config.from_field)
            if requested_code is None:
                continue

            gebiedengroep = gebiedengroepen.get(requested_code)
            if not gebiedengroep:
                continue

            setattr(row, self._config.to_field, gebiedengroep)

        return rows

    def _fetch_gebiedengroepen(self) -> Dict[str, BaseModel]:
        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.Code.in_(self._config.gebiedengroepen_codes))
        rows = self._session.execute(stmt).scalars().all()

        return {r.Code: ObjectStatics.model_validate(r) for r in rows}


class JoinGebiedenGroepenServiceFactory:
    def __init__(self, object_repository: ObjectRepository):
        self._object_repository: ObjectRepository = object_repository

    def create_service(
        self,
        session: Session,
        config: JoinGebiedenGroepenConfig,
    ) -> JoinGebiedenGroepenService:
        return JoinGebiedenGroepenService(
            self._object_repository,
            session,
            config,
        )
