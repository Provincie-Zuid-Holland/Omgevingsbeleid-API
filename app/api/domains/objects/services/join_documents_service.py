from typing import Dict, List, Set
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.domains.objects.types import ObjectStatics
from app.core.tables.objects import ObjectStaticsTable


class JoinDocumentsConfig(BaseModel):
    to_field: str
    from_field: str
    document_codes: Set[str]


class JoinDocumentsService:
    def __init__(
        self,
        session: Session,
        config: JoinDocumentsConfig,
    ):
        self._session: Session = session
        self._config: JoinDocumentsConfig = config

    def join_documents(self, rows: List[BaseModel]) -> List[BaseModel]:
        documents_map: Dict[str, BaseModel] = self._fetch_documents()

        for row in rows:
            document_codes = getattr(row, self._config.from_field) or []
            documents = [documents_map[code] for code in document_codes if code in documents_map]
            setattr(row, self._config.to_field, documents)

        return rows

    def _fetch_documents(self) -> Dict[str, BaseModel]:
        if not self._config.document_codes:
            return {}

        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.Code.in_(self._config.document_codes))
        rows = self._session.execute(stmt).scalars().all()

        return {r.Code: ObjectStatics.model_validate(r) for r in rows}


class JoinDocumentsServiceFactory:
    def create_service(
        self,
        session: Session,
        config: JoinDocumentsConfig,
    ) -> JoinDocumentsService:
        return JoinDocumentsService(session=session, config=config)
