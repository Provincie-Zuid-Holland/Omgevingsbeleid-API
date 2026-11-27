from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.objects.types import ObjectStatics
from app.core.tables.objects import ObjectStaticsTable


class JoinDocumentsConfig(BaseModel):
    to_field: str
    from_field: str
    document_codes: set[str]


class JoinDocumentsService:
    def __init__(
        self,
        session: AsyncSession,
        config: JoinDocumentsConfig,
    ):
        self._session: AsyncSession = session
        self._config: JoinDocumentsConfig = config

    async def join_documents(self, rows: list[BaseModel]) -> list[BaseModel]:
        documents_map: dict[str, BaseModel] = await self._fetch_documents()

        for row in rows:
            document_codes = getattr(row, self._config.from_field) or []
            documents = [documents_map[code] for code in document_codes if code in documents_map]
            setattr(row, self._config.to_field, documents)

        return rows

    async def _fetch_documents(self) -> dict[str, BaseModel]:
        if not self._config.document_codes:
            return {}

        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.code.in_(self._config.document_codes))
        rows = (await self._session.execute(stmt)).scalars().all()

        return {r.code: ObjectStatics.model_validate(r) for r in rows}


class JoinDocumentsServiceFactory:
    def create_service(
        self,
        session: AsyncSession,
        config: JoinDocumentsConfig,
    ) -> JoinDocumentsService:
        return JoinDocumentsService(session=session, config=config)
