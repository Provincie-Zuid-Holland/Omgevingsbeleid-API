from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.base_repository import BaseRepository
from app.core.tables.others import AssetsTable


class AssetRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: UUID) -> AssetsTable | None:
        stmt = select(AssetsTable).filter(AssetsTable.id == idx)
        maybe_asset = (await session.scalars(stmt)).first()
        return maybe_asset

    async def get_by_ids(self, session: AsyncSession, ids: list[UUID]) -> Sequence[AssetsTable]:
        stmt = select(AssetsTable).filter(AssetsTable.id.in_(ids))
        assets = (await session.scalars(stmt)).all()
        return assets

    async def get_by_hash_and_content(self, session: AsyncSession, hash: str, content: str) -> AssetsTable | None:
        stmt = (
            select(AssetsTable)
            .filter(AssetsTable.lookup == hash[0:10])
            .filter(AssetsTable.hash == hash)
            .filter(AssetsTable.content == content)
            .order_by(AssetsTable.created_date.asc(), AssetsTable.id.asc())
            .limit(1)
        )
        maybe_asset = (await session.scalars(stmt)).first()
        return maybe_asset

    async def get_all(self, session: AsyncSession) -> Sequence[AssetsTable]:
        stmt = select(AssetsTable)
        return await self.fetch_all(session, stmt)
