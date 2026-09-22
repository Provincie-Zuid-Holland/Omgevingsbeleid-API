from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.others import AssetsTable


class AssetRepository(BaseRepository):
    def get_by_id(self, session: Session, idx: UUID) -> AssetsTable | None:
        stmt = select(AssetsTable).filter(AssetsTable.id == idx)
        maybe_asset = session.scalars(stmt).first()
        return maybe_asset

    def get_by_ids(self, session: Session, ids: list[UUID]) -> Sequence[AssetsTable]:
        stmt = select(AssetsTable).filter(AssetsTable.id.in_(ids))
        assets = session.scalars(stmt).all()
        return assets

    def get_by_hash_and_content(self, session: Session, hash: str, content: str) -> AssetsTable | None:
        stmt = (
            select(AssetsTable)
            .filter(AssetsTable.lookup == hash[0:10])
            .filter(AssetsTable.hash == hash)
            .filter(AssetsTable.content == content)
        )
        maybe_asset = session.scalars(stmt).first()
        return maybe_asset

    def get_all(self, session: Session) -> Sequence[AssetsTable]:
        stmt = select(AssetsTable)
        return self.fetch_all(session, stmt)
