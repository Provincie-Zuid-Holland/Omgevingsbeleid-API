from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.extensions.areas.dependencies import depends_area_geometry_repository
from app.extensions.areas.repository.area_geometry_repository import AreaGeometryRepository
from app.extensions.html_assets.dependencies import depends_asset_repository
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.publications.dso import (
    DsoAssetsFactory,
    DSOService,
    DsoWerkingsgebiedenFactory,
    OmgevingsvisieTextTemplate,
    ProgrammaTextTemplate,
    TemplateParser,
)
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.repository import PublicationRepository
from app.extensions.publications.repository.ow_object_repository import OWObjectRepository
from app.extensions.publications.repository.publication_object_repository import PublicationObjectRepository


def depends_publication_repository(db: Session = Depends(depends_db)) -> PublicationRepository:
    return PublicationRepository(db)


def depends_publication_object_repository(
    db: Session = Depends(depends_db),
) -> PublicationObjectRepository:
    return PublicationObjectRepository(db)


def depends_ow_object_repository(
    db: Session = Depends(depends_db),
) -> OWObjectRepository:
    return OWObjectRepository(db)


def depends_dso_werkingsgebieden_factory(
    geometry_repository: AreaGeometryRepository = Depends(depends_area_geometry_repository),
) -> DsoWerkingsgebiedenFactory:
    return DsoWerkingsgebiedenFactory(geometry_repository)


def depends_get_parsers() -> TemplateParser:
    return {
        DocumentType.VISION.value: TemplateParser(template_style=OmgevingsvisieTextTemplate()),
        DocumentType.PROGRAM.value: TemplateParser(template_style=ProgrammaTextTemplate()),
    }


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
