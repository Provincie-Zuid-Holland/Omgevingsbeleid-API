from fastapi import Depends
from sqlalchemy.orm import Session

from app.core_old.dependencies import depends_db
from app.extensions.source_werkingsgebieden.repository import (
    GeometryRepository,
    MssqlGeometryRepository,
    SqliteGeometryRepository,
    WerkingsgebiedenRepository,
)


def depends_werkingsgebieden_repository(
    db: Session = Depends(depends_db),
) -> WerkingsgebiedenRepository:
    return WerkingsgebiedenRepository(db)


def depends_geometry_repository(
    db: Session = Depends(depends_db),
) -> GeometryRepository:
    match db.bind.dialect.name:
        case "mssql":
            return MssqlGeometryRepository(db)
        case "sqlite":
            return SqliteGeometryRepository(db)
        case _:
            raise RuntimeError("Unknown database type connected")
