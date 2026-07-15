from collections import defaultdict
from typing import Dict, List

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.domains.others.types import ObjectRelatedFileResponse
from app.core.tables.others import ObjectRelatedFileTable


class JoinRelatedFilesConfig(BaseModel):
    to_field: str
    object_codes: List[str]


class JoinRelatedFilesService:
    def __init__(
        self,
        session: Session,
        config: JoinRelatedFilesConfig,
        rows: List[BaseModel],
    ):
        self._session: Session = session
        self._config: JoinRelatedFilesConfig = config
        self._rows: List[BaseModel] = rows

    def join_related_files(self) -> List[BaseModel]:
        files_map: Dict[str, List[ObjectRelatedFileResponse]] = self._fetch()

        for row in self._rows:
            code: str = getattr(row, "Code")
            setattr(row, self._config.to_field, files_map.get(code, []))

        return self._rows

    def _fetch(self) -> Dict[str, List[ObjectRelatedFileResponse]]:
        stmt = (
            select(ObjectRelatedFileTable)
            .filter(ObjectRelatedFileTable.Code.in_(self._config.object_codes))
            .order_by(ObjectRelatedFileTable.Created_Date.desc())
        )

        db_rows = self._session.execute(stmt).scalars().all()

        files_map: Dict[str, List[ObjectRelatedFileResponse]] = defaultdict(list)
        for db_row in db_rows:
            response = ObjectRelatedFileResponse.model_validate(db_row)
            files_map[db_row.Code].append(response)

        return files_map


class JoinRelatedFilesServiceFactory:
    def create_service(
        self,
        session: Session,
        config: JoinRelatedFilesConfig,
        rows: List[BaseModel],
    ) -> JoinRelatedFilesService:
        return JoinRelatedFilesService(
            session=session,
            config=config,
            rows=rows,
        )
