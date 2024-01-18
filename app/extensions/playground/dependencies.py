from fastapi import Depends

from app.extensions.playground.services.dso_werkingsgebieden_factory import DsoWerkingsgebiedenFactory
from app.extensions.werkingsgebieden.dependencies import depends_geometry_repository
from app.extensions.werkingsgebieden.repository.geometry_repository import GeometryRepository


def depends_dso_werkingsgebieden_factory(
    geometry_repository: GeometryRepository = Depends(depends_geometry_repository),
) -> DsoWerkingsgebiedenFactory:
    return DsoWerkingsgebiedenFactory(geometry_repository)
