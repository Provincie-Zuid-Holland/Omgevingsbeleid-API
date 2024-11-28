from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db

from .repository import StorageFileRepository


def depends_storage_file_repository(
    db: Session = Depends(depends_db),
) -> StorageFileRepository:
    return StorageFileRepository(db)
