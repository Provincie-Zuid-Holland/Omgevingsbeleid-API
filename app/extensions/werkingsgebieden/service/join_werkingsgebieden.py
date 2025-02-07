from dataclasses import dataclass
from typing import Dict, List, Optional, Type, get_args

from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.dynamic.config.models import DynamicObjectModel, Model
from app.dynamic.db import ObjectsTable


@dataclass
class Config:
    werkingsgebied_codes: List[str]
    from_field: str
    to_field: str


class JoinWerkingsgebiedenService:
    def __init__(
        self,
        db: Session,
        rows: List[BaseModel],
        response_model: Model,
    ):
        self._db: Session = db
        self._rows: List[BaseModel] = rows
        self._response_model: Model = response_model

    def join_werkingsgebieden(self) -> List[BaseModel]:
        config: Optional[Config] = self._collect_config()
        if not config:
            return self._rows

        if len(config.werkingsgebied_codes) == 0:
            return self._rows

        werkingsgebieden: Dict[str, BaseModel] = self._fetch_werkingsgebieden(config)

        result_rows: List[BaseModel] = []
        for row in self._rows:
            werkingsgebied_code = getattr(row, config.from_field)
            if werkingsgebied_code in werkingsgebieden:
                werkingsgebied = werkingsgebieden[werkingsgebied_code]
                getattr(row, config.to_field).append(werkingsgebied)
            result_rows.append(row)

        return result_rows

    def _collect_config(self) -> Optional[Config]:
        if not isinstance(self._response_model, DynamicObjectModel):
            return None
        if not "join_werkingsgebieden" in self._response_model.service_config:
            return None

        join_werkingsgebieden_config: dict = self._response_model.service_config["join_werkingsgebieden"]
        to_field: str = join_werkingsgebieden_config["to_field"]
        from_field: str = join_werkingsgebieden_config["from_field"]

        werkingsgebied_codes: List[str] = list(set([getattr(r, from_field) for r in self._rows]))
        werkingsgebied_codes: List[str] = [c for c in werkingsgebied_codes if c is not None]

        return Config(
            werkingsgebied_codes,
            from_field,
            to_field,
        )

    def _fetch_werkingsgebieden(self, config: Config) -> Dict[str, BaseModel]:
        werkingsgebied_annotation = self._response_model.pydantic_model.__annotations__.get(config.to_field)
        werkingsgebied_model: Type[BaseModel] = get_args(werkingsgebied_annotation)[0]

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
                ObjectsTable.Code.in_(config.werkingsgebied_codes),
            )
            .subquery()
        )

        stmt = select(subq).filter(subq.c._RowNumber == 1)

        rows = self._db.execute(stmt).all()
        result: Dict[str, BaseModel] = {r.Code: werkingsgebied_model.from_orm(r) for r in rows}

        return result
