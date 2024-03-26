from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.extensions.html_assets.db.tables import AssetsTable


class AssetRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_by_uuid(self, uuid: UUID) -> Optional[AssetsTable]:
        stmt = select(AssetsTable).filter(AssetsTable.UUID == uuid)
        maybe_asset = self._db.scalars(stmt).first()
        return maybe_asset

    def get_by_uuids(self, uuids: List[UUID]) -> List[AssetsTable]:
        stmt = select(AssetsTable).filter(AssetsTable.UUID.in_(uuids))
        assets = self._db.scalars(stmt).all()
        return assets

    def get_by_hash_and_content(self, hash: str, content: str) -> Optional[AssetsTable]:
        stmt = (
            select(AssetsTable)
            .filter(AssetsTable.Lookup == hash[0:10])
            .filter(AssetsTable.Hash == hash)
            .filter(AssetsTable.Content == content)
        )
        maybe_asset = self._db.scalars(stmt).first()
        return maybe_asset
