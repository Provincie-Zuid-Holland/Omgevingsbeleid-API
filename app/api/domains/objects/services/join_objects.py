from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.objects.types import ObjectStatics
from app.core.tables.objects import ObjectStaticsTable


class JoinObjectsConfig(BaseModel):
    object_codes: set[str]
    from_field: str
    to_field: str


class JoinObjectsService:
    def __init__(
        self,
        object_repository: ObjectRepository,
        session: AsyncSession,
        config: JoinObjectsConfig,
    ):
        self._object_repository: ObjectRepository = object_repository
        self._session: AsyncSession = session
        self._config: JoinObjectsConfig = config

    async def join_objects(self, rows: list[BaseModel]) -> list[BaseModel]:
        if len(self._config.object_codes) == 0:
            return rows

        objects: dict[str, BaseModel] = await self._fetch_objects()

        result_rows: list[BaseModel] = []
        for row in rows:
            requested_codes: list[str] = getattr(row, self._config.from_field)

            result_for_row: list[BaseModel] = []
            for object_code in requested_codes:
                object_in = objects.get(object_code)
                if not object_in:
                    continue
                result_for_row.append(object_in)

            setattr(row, self._config.to_field, result_for_row)
            result_rows.append(row)

        return result_rows

    async def _fetch_objects(self) -> dict[str, BaseModel]:
        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.code.in_(self._config.object_codes))
        rows = (await self._session.execute(stmt)).scalars().all()

        return {r.code: ObjectStatics.model_validate(r) for r in rows}


class JoinObjectsServiceFactory:
    def __init__(self, object_repository: ObjectRepository):
        self._object_repository: ObjectRepository = object_repository

    def create_service(
        self,
        session: AsyncSession,
        config: JoinObjectsConfig,
    ) -> JoinObjectsService:
        return JoinObjectsService(
            self._object_repository,
            session,
            config,
        )
