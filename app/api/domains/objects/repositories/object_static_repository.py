from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.base_repository import BaseRepository
from app.api.types import PreparedQuery
from app.core.tables.objects import ObjectStaticsTable


class ObjectStaticRepository(BaseRepository):
    async def get_by_object_type_and_id(
        self, session: AsyncSession, object_type: str, object_id: int
    ) -> ObjectStaticsTable | None:
        prepared_query: PreparedQuery = self.prepare_by_object_type_and_id(object_type, object_id)
        return await self.fetch_first(session, prepared_query.query)

    def prepare_by_object_type_and_id(self, object_type: str, object_id: int) -> PreparedQuery:
        stmt = (
            select(ObjectStaticsTable)
            .filter(ObjectStaticsTable.object_type == object_type)
            .filter(ObjectStaticsTable.object_id == object_id)
        )
        return PreparedQuery(
            query=stmt,
            aliased_ref=ObjectStaticsTable,
        )

    async def get_by_type_and_owner(
        self, session: AsyncSession, object_type: str | None = None, owner_uuid: UUID | None = None
    ) -> list[ObjectStaticsTable]:
        stmt = select(ObjectStaticsTable)

        if owner_uuid:
            type_filter = or_(
                ObjectStaticsTable.owner_1_id == owner_uuid,
                ObjectStaticsTable.owner_2_id == owner_uuid,
            )
            stmt = stmt.filter(type_filter)

        if object_type:
            stmt = stmt.filter(ObjectStaticsTable.object_type == object_type)

        return await self.fetch_all(session, stmt)

    async def get_by_source(self, session: AsyncSession, source_key: str) -> ObjectStaticsTable | None:
        stmt = select(ObjectStaticsTable).filter(ObjectStaticsTable.source_identifier == source_key)
        return await self.fetch_first(session, stmt)

    async def does_codes_exists(self, session: AsyncSession, codes: set[str]) -> tuple[bool, set[str]]:
        if not len(codes):
            return True, set()

        stmt = select(ObjectStaticsTable.code).where(ObjectStaticsTable.code.in_(codes))
        existing: set[str] = set((await session.execute(stmt)).scalars())
        missing: set[str] = set(codes) - existing

        return len(missing) == 0, missing
