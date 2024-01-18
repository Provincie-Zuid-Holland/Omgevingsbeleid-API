from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.extensions.werkingsgebieden.repository import WerkingsgebiedenRepository
from app.extensions.werkingsgebieden.repository.geometry_repository import GeometryRepository
from app.extensions.werkingsgebieden.repository.mssql_geometry_repository import MssqlGeometryRepository
from app.extensions.werkingsgebieden.repository.sqlite_geometry_repository import SqliteGeometryRepository


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
