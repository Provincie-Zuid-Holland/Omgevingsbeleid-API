from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.extensions.html_assets.dependencies import depends_asset_repository
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.publications.dso import (
    DsoAssetsFactory,
    DSOService,
    DsoWerkingsgebiedenFactory,
    OmgevingsprogrammaTextTemplate,
    OmgevingsvisieTextTemplate,
    TemplateParser,
)
from app.extensions.publications.repository import PublicationRepository
from app.extensions.publications.repository.publication_object_repository import PublicationObjectRepository
from app.extensions.source_werkingsgebieden.dependencies import depends_geometry_repository
from app.extensions.source_werkingsgebieden.repository.geometry_repository import GeometryRepository


def depends_publication_repository(db: Session = Depends(depends_db)) -> PublicationRepository:
    return PublicationRepository(db)


def depends_publication_object_repository(
    db: Session = Depends(depends_db),
) -> PublicationObjectRepository:
    return PublicationObjectRepository(db)


def depends_dso_werkingsgebieden_factory(
    geometry_repository: GeometryRepository = Depends(depends_geometry_repository),
) -> DsoWerkingsgebiedenFactory:
    return DsoWerkingsgebiedenFactory(geometry_repository)


def depends_get_parsers() -> TemplateParser:
    template_parsers = (
        {
            "Omgevingsvisie": TemplateParser(template_style=OmgevingsvisieTextTemplate()),
            "Omgevingsprogramma": TemplateParser(template_style=OmgevingsprogrammaTextTemplate()),
        },
    )
    return template_parsers


def depends_dso_assets_factory(
    asset_repository: AssetRepository = Depends(depends_asset_repository),
) -> DsoAssetsFactory:
    return DsoAssetsFactory(asset_repository)


def depends_dso_service(
    template_parsers=Depends(depends_get_parsers),
    dso_werkingsgebieden_factory=Depends(depends_dso_werkingsgebieden_factory),
    dso_assets_factory=Depends(depends_dso_assets_factory),
) -> DSOService:
    return DSOService(template_parsers, dso_werkingsgebieden_factory, dso_assets_factory)
