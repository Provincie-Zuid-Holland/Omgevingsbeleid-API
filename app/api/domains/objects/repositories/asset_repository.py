from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tables.others import AssetsTable


class AssetRepository:
    def get_by_uuid(self, session: Session, uuid: UUID) -> Optional[AssetsTable]:
        stmt = select(AssetsTable).filter(AssetsTable.UUID == uuid)
        maybe_asset = session.scalars(stmt).first()
        return maybe_asset

    def get_by_uuids(self, session: Session, uuids: List[UUID]) -> Sequence[AssetsTable]:
        stmt = select(AssetsTable).filter(AssetsTable.UUID.in_(uuids))
        assets = session.scalars(stmt).all()
        return assets

    def get_by_hash_and_content(self, session: Session, hash: str, content: str) -> Optional[AssetsTable]:
        stmt = (
            select(AssetsTable)
            .filter(AssetsTable.Lookup == hash[0:10])
            .filter(AssetsTable.Hash == hash)
            .filter(AssetsTable.Content == content)
        )
        maybe_asset = session.scalars(stmt).first()
        return maybe_asset
