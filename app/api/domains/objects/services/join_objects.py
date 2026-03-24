from typing import Dict, List, Set

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.objects.types import ObjectStatics
from app.core.tables.objects import ObjectStaticsTable


class JoinObjectsConfig(BaseModel):
    object_codes: Set[str]
    from_field: str
    to_field: str


class JoinObjectsService:
    def __init__(
        self,
        object_repository: ObjectRepository,
        session: Session,
        config: JoinObjectsConfig,
    ):
        self._object_repository: ObjectRepository = object_repository
        self._session: Session = session
        self._config: JoinObjectsConfig = config

    def join_objects(self, rows: List[BaseModel]) -> List[BaseModel]:
        if len(self._config.object_codes) == 0:
            return rows

        objects: Dict[str, BaseModel] = self._fetch_objects()

        result_rows: List[BaseModel] = []
        for row in rows:
            requested_codes: List[str] = getattr(row, self._config.from_field)

            result_for_row: List[BaseModel] = []
            for object_code in requested_codes:
                object_in = objects.get(object_code)
                if not object_in:
                    continue
                result_for_row.append(object_in)

            setattr(row, self._config.to_field, result_for_row)
            result_rows.append(row)

        return result_rows

    def _fetch_objects(self) -> Dict[str, BaseModel]:
        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.Code.in_(self._config.object_codes))
        rows = self._session.execute(stmt).scalars().all()

        return {r.Code: ObjectStatics.model_validate(r) for r in rows}


class JoinObjectsServiceFactory:
    def __init__(self, object_repository: ObjectRepository):
        self._object_repository: ObjectRepository = object_repository

    def create_service(
        self,
        session: Session,
        config: JoinObjectsConfig,
    ) -> JoinObjectsService:
        return JoinObjectsService(
            self._object_repository,
            session,
            config,
        )
