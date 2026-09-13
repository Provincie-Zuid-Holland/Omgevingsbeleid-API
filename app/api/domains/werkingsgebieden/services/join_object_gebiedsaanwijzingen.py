from collections.abc import Iterator
from datetime import UTC, datetime

from bs4 import BeautifulSoup
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import func, or_

from app.core.tables.objects import ObjectsTable


class JoinObjectGebiedsaanwijzingenConfig(BaseModel):
    from_fields: set[str]
    to_field: str
    to_model: type[BaseModel]


def _get_aanwijzing_codes(html: str) -> set[str]:
    result: set[str] = set()

    try:
        soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
        for aanwijzing_html in soup.select('a[data-hint-type="gebiedsaanwijzing"]'):
            aanwijzing_code: str = str(aanwijzing_html.get("data-code", ""))
            if not aanwijzing_code:
                continue
            result.add(aanwijzing_code)
    except TypeError:
        pass

    return result


class JoinObjectGebiedsaanwijzingenService:
    def __init__(
        self,
        session: Session,
        config: JoinObjectGebiedsaanwijzingenConfig,
    ):
        self._session: Session = session
        self._config: JoinObjectGebiedsaanwijzingenConfig = config

    def join_gebiedsaanwijzingen(self, rows: list[BaseModel]) -> list[BaseModel]:
        if not rows:
            return rows
        if len(rows) != 1:
            raise RuntimeError("JoinObjectGebiedsaanwijzingenService should only be used for single results")

        row = rows[0]
        collected_aanwijzing_codes: set[str] = set()

        for field_key in self._config.from_fields:
            field_value: str = getattr(row, field_key)
            fields_aanwijzing_codes: set[str] = _get_aanwijzing_codes(field_value)
            collected_aanwijzing_codes.update(fields_aanwijzing_codes)

        # If we dont have any then we wont need to merge any data back in
        if len(collected_aanwijzing_codes) == 0:
            return rows

        gebieden = self._resolve_codes(collected_aanwijzing_codes)
        setattr(row, self._config.to_field, gebieden)
        rows[0] = row

        return rows

    def _resolve_codes(self, aanwijzing_codes: set[str]):
        gebied_codes: set[str] = set()
        gebiedengroep_codes: set[str] = set()

        gebiedsaanwijzingen = self._get_latests(aanwijzing_codes)
        for gebiedsaanwijzing in gebiedsaanwijzingen:
            refs: list[str] = gebiedsaanwijzing.Target_Codes
            for ref in refs:
                object_type, _ = ref.split("-", 1)
                match object_type:
                    case "gebiedengroep":
                        gebiedengroep_codes.add(ref)
                    case "gebied":
                        gebied_codes.add(ref)

        if gebiedengroep_codes:
            gebiedengroepen = self._get_latests(gebiedengroep_codes)
            for gebiedengroep in gebiedengroepen:
                refs: list[str] = gebiedengroep.Gebieden
                gebied_codes.update(refs)

        if not gebied_codes:
            return []

        gebieden = self._get_latests(gebied_codes)
        gebieden_parsed = [self._config.to_model.model_validate(gebied) for gebied in gebieden]
        return gebieden_parsed

    def _get_latests(self, codes: set[str]) -> Iterator[ObjectsTable]:
        timepoint = datetime.now(UTC)

        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.Code,
                order_by=desc(ObjectsTable.Modified_Date),
            )
            .label("_RowNumber")
        )

        subq = (
            select(ObjectsTable, row_number)
            .filter(ObjectsTable.Code.in_(codes))
            .filter(ObjectsTable.Start_Validity <= timepoint)
        ).subquery()

        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > timepoint,
                    subq.c.End_Validity.is_(None),
                )
            )
            .order_by(desc(subq.c.Modified_Date))
        )
        result = self._session.execute(stmt)
        return result.scalars()


class JoinObjectGebiedsaanwijzingenServiceFactory:
    def create_service(
        self,
        session: Session,
        config: JoinObjectGebiedsaanwijzingenConfig,
    ) -> JoinObjectGebiedsaanwijzingenService:
        return JoinObjectGebiedsaanwijzingenService(
            session,
            config,
        )
