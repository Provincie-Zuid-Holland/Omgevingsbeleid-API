from fastapi import Depends
from sqlalchemy.orm import Session

from app.core_old.dependencies import depends_db

from .repository import (
    AreaGeometryRepository,
    AreaRepository,
    MssqlAreaGeometryRepository,
    SqliteAreaGeometryRepository,
)


def depends_area_repository(
    db: Session = Depends(depends_db),
) -> AreaRepository:
    return AreaRepository(db)


def depends_area_geometry_repository(
    db: Session = Depends(depends_db),
) -> AreaGeometryRepository:
    match db.bind.dialect.name:
        case "mssql":
            return MssqlAreaGeometryRepository(db)
        case "sqlite":
            return SqliteAreaGeometryRepository(db)
        case _:
            raise RuntimeError("Unknown database type connected")
