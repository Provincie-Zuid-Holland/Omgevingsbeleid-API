from typing import Set, List, Sequence, Dict

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
        session: Session,
        config: JoinGebiedsaanwijzingenConfig,
    ):
        self._session: Session = session
        self._config: JoinGebiedsaanwijzingenConfig = config

    def join_gebiedsaanwijzingen(self, rows: List[BaseModel]) -> List[BaseModel]:
        if len(rows) <= 0:
            return rows
        result_rows: List[BaseModel] = []
        all_aanwijzing_codes: Set[str] = set()
        aanwijzing_codes_per_object: Dict[str, Set[str]] = {}

        for row in rows:
            aanwijzing_codes_current_row: Set[str] = set()
            for field in self._config.from_fields:
                try:
                    soup: BeautifulSoup = BeautifulSoup(getattr(row, field), "html.parser")
                    for aanwijzing_html in soup.select('a[data-hint-type="gebiedsaanwijzing"]'):
                        aanwijzing_code: str = str(aanwijzing_html.get("data-code", ""))
                        if not aanwijzing_code:
                            continue
                        all_aanwijzing_codes.add(aanwijzing_code)
                        aanwijzing_codes_current_row.add(aanwijzing_code)
                except TypeError:
                    continue
            aanwijzing_codes_per_object[getattr(row, "Code")] = aanwijzing_codes_current_row

        if len(all_aanwijzing_codes) <= 0:
            return rows

        gebiedsaanwijzingen: Dict[str, ObjectStatics] = self._fetch_object_statics(all_aanwijzing_codes)

        for row in rows:
            object_code: str = getattr(row, "Code")
            aanwijzing_statics: List[ObjectStatics] = []
            for aanwijzing_code in aanwijzing_codes_per_object[object_code]:
                object_statics: ObjectStatics = gebiedsaanwijzingen.get(aanwijzing_code)
                if not object_statics:
                    continue
                aanwijzing_statics.append(object_statics)
            setattr(row, self._config.to_field, aanwijzing_statics)
            result_rows.append(row)

        return result_rows

    def _fetch_object_statics(self, aanwijzing_codes: Set[str]) -> Dict[str, ObjectStatics]:
        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.Code.in_(aanwijzing_codes))
        rows: Sequence[ObjectStaticsTable] = self._session.execute(stmt).scalars().all()
        return {r.Code: ObjectStatics.model_validate(r) for r in rows}


class JoinGebiedsaanwijzingenServiceFactory:
    def create_service(
        self,
        session: Session,
        config: JoinGebiedsaanwijzingenConfig,
    ) -> JoinGebiedsaanwijzingenService:
        return JoinGebiedsaanwijzingenService(
            session,
            config,
        )
