from typing import Dict, List, Set, Type
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.services.models_provider import ModelsProvider
from app.core.tables.objects import ObjectsTable


class JoinDocumentsConfig(BaseModel):
    to_field: str
    from_field: str
    model_id: str
    document_codes: Set[str]


class JoinDocumentsService:
    def __init__(
        self,
        models_provider: ModelsProvider,
        session: Session,
        config: JoinDocumentsConfig,
    ):
        self._models_provider: ModelsProvider = models_provider
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

        document_model: Type[BaseModel] = self._models_provider.get_pydantic_model(self._config.model_id)
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
            .filter(ObjectsTable.Code.in_(self._config.document_codes))
            .subquery()
        )

        stmt = select(subq).filter(subq.c._RowNumber == 1)
        rows = self._session.execute(stmt).all()

        return {r.Code: document_model.model_validate(r) for r in rows}


class JoinDocumentsServiceFactory:
    def __init__(self, models_provider: ModelsProvider):
        self._models_provider: ModelsProvider = models_provider

    def create_service(
        self,
        session: Session,
        config: JoinDocumentsConfig,
    ) -> JoinDocumentsService:
        return JoinDocumentsService(
            models_provider=self._models_provider,
            session=session,
            config=config,
        )
