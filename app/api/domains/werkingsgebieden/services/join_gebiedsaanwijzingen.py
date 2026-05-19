from typing import Set, List

from bs4 import BeautifulSoup
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories import ObjectStaticRepository
from app.api.domains.objects.types import ObjectStatics
from app.core.tables.objects import ObjectStaticsTable


class JoinGebiedsaanwijzingenConfig(BaseModel):
    from_fields: Set[str]
    to_field: str


class JoinGebiedsaanwijzingenService:
    def __init__(
        self,
        object_static_repository: ObjectStaticRepository,
        session: Session,
        config: JoinGebiedsaanwijzingenConfig,
    ):
        self._object_static_repository: ObjectStaticRepository = object_static_repository
        self._session: Session = session
        self._config: JoinGebiedsaanwijzingenConfig = config

    def join_gebiedsaanwijzingen(self, rows: List[BaseModel]):
        if len(rows) <= 0:
            return rows

        result_rows: List[BaseModel] = []
        for row in rows:
            aanwijzing_codes: Set[str] = set()
            for field in self._config.from_fields:
                soup = BeautifulSoup(getattr(row, field), "html.parser")
                for aanwijzing_html in soup.select('a[data-hint-type="gebiedsaanwijzing"]'):
                    aanwijzing_code: str = str(aanwijzing_html.get("data-code", ""))
                    if not aanwijzing_code:
                        continue
                    aanwijzing_codes.add(aanwijzing_code)
            if aanwijzing_codes:
                object_statics = self._fetch_object_statics(aanwijzing_codes)
                setattr(row, self._config.to_field, object_statics)
            result_rows.append(row)
        return result_rows

    def _fetch_object_statics(self, aanwijzing_codes: Set[str]) -> List[BaseModel]:
        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.Code.in_(aanwijzing_codes))
        rows = self._session.execute(stmt).scalars().all()
        return [ObjectStatics.model_validate(r) for r in rows]


class JoinGebiedsaanwijzingenServiceFactory:
    def __init__(self, object_static_repository: ObjectStaticRepository):
        self._object_static_repository: ObjectStaticRepository = object_static_repository

    def create_service(
        self,
        session: Session,
        config: JoinGebiedsaanwijzingenConfig,
    ) -> JoinGebiedsaanwijzingenService:
        return JoinGebiedsaanwijzingenService(
            self._object_static_repository,
            session,
            config,
        )
