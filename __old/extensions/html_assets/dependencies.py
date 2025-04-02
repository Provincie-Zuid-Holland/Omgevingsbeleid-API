from fastapi import Depends
from sqlalchemy.orm import Session

from app.core_old.dependencies import depends_db
from app.extensions.html_assets.repository.assets_repository import AssetRepository


def depends_asset_repository(db: Session = Depends(depends_db)) -> AssetRepository:
    return AssetRepository(db)
