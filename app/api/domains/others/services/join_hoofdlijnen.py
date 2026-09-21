from collections.abc import Sequence
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.domains.others.types import Hoofdlijn
from app.core.tables.others import HoofdlijnTable


class JoinHoofdlijnenConfig(BaseModel):
    from_fields: set[str]
    to_field: str


class JoinHoofdlijnenService:
    def __init__(
        self,
        session: Session,
        config: JoinHoofdlijnenConfig,
    ):
        self._session: Session = session
        self._config: JoinHoofdlijnenConfig = config

    def join_hoofdlijnen(self, rows: list[BaseModel]) -> list[BaseModel]:
        if len(rows) <= 0:
            return rows
        result_rows: list[BaseModel] = []
        all_hoofdlijn_codes: set[str] = set()
        hoofdlijn_codes_per_object: dict[str, set[str]] = {}

        for row in rows:
            hoofdlijn_codes_current_row: set[str] = set()
            for field in self._config.from_fields:
                hoofdlijn_ids: list[str] = getattr(row, field)
                if len(hoofdlijn_ids) == 0:
                    continue
                for hoofdlijn_id in hoofdlijn_ids:
                    all_hoofdlijn_codes.add(hoofdlijn_id)
                    hoofdlijn_codes_current_row.add(hoofdlijn_id)
            hoofdlijn_codes_per_object[row.Code] = hoofdlijn_codes_current_row

        if len(all_hoofdlijn_codes) <= 0:
            return rows

        hoofdlijnen: dict[UUID, Hoofdlijn] = self._fetch_hoofdlijnen(all_hoofdlijn_codes)

        for row in rows:
            object_code: str = row.Code
            hoofdlijnen_statics: list[Hoofdlijn] = []
            for hoofdlijn_id in hoofdlijn_codes_per_object[object_code]:
                hoofdlijn_statics: Hoofdlijn | None = hoofdlijnen.get(UUID(hoofdlijn_id))
                if not hoofdlijn_statics:
                    continue
                hoofdlijnen_statics.append(hoofdlijn_statics)
            setattr(row, self._config.to_field, hoofdlijnen_statics)
            result_rows.append(row)

        return result_rows

    def _fetch_hoofdlijnen(self, hoofdlijnen_ids: set[str]) -> dict[UUID, Hoofdlijn]:
        hoofdlijnen_uuids: set[UUID] = {UUID(idx) for idx in hoofdlijnen_ids}
        stmt = select(HoofdlijnTable).filter(HoofdlijnTable.UUID.in_(hoofdlijnen_uuids))
        rows: Sequence[HoofdlijnTable] = self._session.execute(stmt).scalars().all()
        return {r.UUID: Hoofdlijn.model_validate(r) for r in rows}


class JoinHoofdlijnenServiceFactory:
    def create_service(
        self,
        session: Session,
        config: JoinHoofdlijnenConfig,
    ) -> JoinHoofdlijnenService:
        return JoinHoofdlijnenService(
            session=session,
            config=config,
        )
