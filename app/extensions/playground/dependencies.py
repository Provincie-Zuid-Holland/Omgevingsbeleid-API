from fastapi import Depends

from app.extensions.html_assets.dependencies import depends_asset_repository
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.playground.services.dso_assets_factory import DsoAssetsFactory
from app.extensions.playground.services.dso_werkingsgebieden_factory import DsoWerkingsgebiedenFactory
from app.extensions.playground.services.input_data_service import InputDataService
from app.extensions.playground.services.template_parser import TemplateParser
from app.extensions.playground.templates.omgevingsprogramma import OmgevingsprogrammaTextTemplate
from app.extensions.playground.templates.omgevingsvisie import OmgevingsvisieTextTemplate
from app.extensions.werkingsgebieden.dependencies import depends_geometry_repository
from app.extensions.werkingsgebieden.repository.geometry_repository import GeometryRepository


def depends_dso_werkingsgebieden_factory(
    geometry_repository: GeometryRepository = Depends(depends_geometry_repository),
) -> DsoWerkingsgebiedenFactory:
    return DsoWerkingsgebiedenFactory(geometry_repository)


def depends_omgevingsvisie_template_parser() -> TemplateParser:
    return TemplateParser(
        template_style=OmgevingsvisieTextTemplate(),
    )


def depends_omgevingsprogramma_template_parser() -> TemplateParser:
    return TemplateParser(
        template_style=OmgevingsprogrammaTextTemplate(),
    )


def depends_dso_assets_factory(
    asset_repository: AssetRepository = Depends(depends_asset_repository),
) -> DsoAssetsFactory:
    return DsoAssetsFactory(asset_repository)


def depends_input_data_service() -> InputDataService:
    return InputDataService()
