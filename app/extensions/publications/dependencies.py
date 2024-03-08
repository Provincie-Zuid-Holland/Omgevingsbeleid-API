import uuid
from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.dependencies import depends_main_config
from app.extensions.areas.dependencies import depends_area_geometry_repository
from app.extensions.areas.repository.area_geometry_repository import AreaGeometryRepository
from app.extensions.html_assets.dependencies import depends_asset_repository
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.publications.repository import PublicationRepository, PublicationTemplateRepository
from app.extensions.publications.repository.publication_aoj_repository import PublicationAOJRepository
from app.extensions.publications.repository.publication_environment_repository import PublicationEnvironmentRepository
from app.extensions.publications.repository.publication_object_repository import PublicationObjectRepository
from app.extensions.publications.repository.publication_version_repository import PublicationVersionRepository
from app.extensions.publications.services.act_frbr_provider import ActFrbrProvider
from app.extensions.publications.services.assets.asset_remove_transparency import AssetRemoveTransparency
from app.extensions.publications.services.assets.publication_asset_provider import PublicationAssetProvider
from app.extensions.publications.services.bill_frbr_provider import BillFrbrProvider
from app.extensions.publications.services.package_builder_factory import PackageBuilderFactory
from app.extensions.publications.services.package_version_defaults_provider import PackageVersionDefaultsProvider
from app.extensions.publications.services.publication_data_provider import PublicationDataProvider
from app.extensions.publications.services.template_parser import TemplateParser
from app.extensions.publications.services.werkingsgebieden_provider import PublicationWerkingsgebiedenProvider
from app.extensions.publications.tables import PublicationPackageTable, PublicationTemplateTable
from app.extensions.publications.tables.tables import (
    PublicationAreaOfJurisdictionTable,
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationVersionTable,
)


def depends_publication_template_repository(db: Session = Depends(depends_db)) -> PublicationTemplateRepository:
    return PublicationTemplateRepository(db)


def depends_publication_template(
    template_uuid: uuid.UUID,
    repository: PublicationTemplateRepository = Depends(depends_publication_template_repository),
) -> PublicationTemplateTable:
    maybe_template: Optional[PublicationTemplateTable] = repository.get_by_uuid(template_uuid)
    if not maybe_template:
        raise HTTPException(status_code=404, detail="Publication template niet gevonden")
    return maybe_template


def depends_publication_environment_repository(db: Session = Depends(depends_db)) -> PublicationEnvironmentRepository:
    return PublicationEnvironmentRepository(db)


def depends_publication_environment(
    environment_uuid: uuid.UUID,
    repository: PublicationEnvironmentRepository = Depends(depends_publication_environment_repository),
) -> PublicationEnvironmentTable:
    maybe_environment: Optional[PublicationEnvironmentTable] = repository.get_by_uuid(environment_uuid)
    if not maybe_environment:
        raise HTTPException(status_code=404, detail="Publication environment niet gevonden")
    return maybe_environment


def depends_publication_aoj_repository(db: Session = Depends(depends_db)) -> PublicationAOJRepository:
    return PublicationAOJRepository(db)


def depends_publication_aoj(
    environment_uuid: uuid.UUID,
    repository: PublicationAOJRepository = Depends(depends_publication_aoj_repository),
) -> PublicationAreaOfJurisdictionTable:
    maybe_environment: Optional[PublicationAreaOfJurisdictionTable] = repository.get_by_uuid(environment_uuid)
    if not maybe_environment:
        raise HTTPException(status_code=404, detail="Publication area of jurisdiction niet gevonden")
    return maybe_environment


def depends_publication_repository(db: Session = Depends(depends_db)) -> PublicationRepository:
    return PublicationRepository(db)


def depends_publication(
    publication_uuid: uuid.UUID,
    repository: PublicationRepository = Depends(depends_publication_repository),
) -> PublicationTable:
    maybe_publication: Optional[PublicationTable] = repository.get_by_uuid(publication_uuid)
    if not maybe_publication:
        raise HTTPException(status_code=404, detail="Publication niet gevonden")
    return maybe_publication


def depends_publication_version_repository(db: Session = Depends(depends_db)) -> PublicationVersionRepository:
    return PublicationVersionRepository(db)


def depends_publication_version(
    version_uuid: uuid.UUID,
    repository: PublicationVersionRepository = Depends(depends_publication_version_repository),
) -> PublicationVersionTable:
    maybe_version: Optional[PublicationVersionTable] = repository.get_by_uuid(version_uuid)
    if not maybe_version:
        raise HTTPException(status_code=404, detail="Publication version niet gevonden")
    return maybe_version


def depends_publication_package(
    package_uuid: uuid.UUID,
    publication_repository: PublicationRepository = Depends(depends_publication_repository),
) -> PublicationPackageTable:
    package: Optional[PublicationPackageTable] = publication_repository.get_publication_package(package_uuid)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


def depends_package_version_defaults_provider(
    main_config: dict = Depends(depends_main_config),
) -> PackageVersionDefaultsProvider:
    defaults: dict = main_config["publication"]["defaults"]
    return PackageVersionDefaultsProvider(defaults)


def depends_publication_object_repository(
    db: Session = Depends(depends_db),
) -> PublicationObjectRepository:
    return PublicationObjectRepository(db)


def depends_bill_frbr_provider() -> BillFrbrProvider:
    return BillFrbrProvider()


def depends_act_frbr_provider() -> ActFrbrProvider:
    return ActFrbrProvider()


def depends_publication_asset_provider(
    asset_repository: AssetRepository = Depends(depends_asset_repository),
) -> PublicationAssetProvider:
    return PublicationAssetProvider(
        asset_repository,
        AssetRemoveTransparency(),
    )


def depends_publication_werkingsgebieden_provider(
    area_geometry_repository: AreaGeometryRepository = Depends(depends_area_geometry_repository),
) -> PublicationWerkingsgebiedenProvider:
    return PublicationWerkingsgebiedenProvider(
        area_geometry_repository,
    )


def depends_publication_data_provider(
    publication_object_repository: PublicationObjectRepository = Depends(depends_publication_object_repository),
    publication_asset_provider: PublicationAssetProvider = Depends(depends_publication_asset_provider),
    publication_werkingsgebieden_provider: PublicationWerkingsgebiedenProvider = Depends(
        depends_publication_werkingsgebieden_provider
    ),
    publication_aoj_repository: PublicationAOJRepository = Depends(depends_publication_aoj_repository),
) -> PublicationDataProvider:
    return PublicationDataProvider(
        publication_object_repository,
        publication_asset_provider,
        publication_werkingsgebieden_provider,
        publication_aoj_repository,
        TemplateParser(),
    )


def depends_package_builder_factory(
    db: Session = Depends(depends_db),
    bill_frbr_provider: BillFrbrProvider = Depends(depends_bill_frbr_provider),
    act_frbr_provider: ActFrbrProvider = Depends(depends_act_frbr_provider),
    publication_data_provider: PublicationDataProvider = Depends(depends_publication_data_provider),
) -> PackageBuilderFactory:
    return PackageBuilderFactory(
        db,
        bill_frbr_provider,
        act_frbr_provider,
        publication_data_provider,
    )
