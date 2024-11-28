import uuid
from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db, depends_main_config, depends_settings
from app.core.settings.dynamic_settings import DynamicSettings
from app.extensions.areas.dependencies import depends_area_repository
from app.extensions.areas.repository.area_geometry_repository import AreaGeometryRepository
from app.extensions.attachments.dependencies import depends_storage_file_repository
from app.extensions.attachments.repository.storage_file_repository import StorageFileRepository
from app.extensions.html_assets.dependencies import depends_asset_repository
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.publications.repository import PublicationRepository, PublicationTemplateRepository
from app.extensions.publications.repository.publication_act_package_repository import PublicationActPackageRepository
from app.extensions.publications.repository.publication_act_report_repository import PublicationActReportRepository
from app.extensions.publications.repository.publication_act_repository import PublicationActRepository
from app.extensions.publications.repository.publication_act_version_repository import PublicationActVersionRepository
from app.extensions.publications.repository.publication_announcement_package_repository import (
    PublicationAnnouncementPackageRepository,
)
from app.extensions.publications.repository.publication_announcement_report_repository import (
    PublicationAnnouncementReportRepository,
)
from app.extensions.publications.repository.publication_announcement_repository import PublicationAnnouncementRepository
from app.extensions.publications.repository.publication_aoj_repository import PublicationAOJRepository
from app.extensions.publications.repository.publication_environment_repository import PublicationEnvironmentRepository
from app.extensions.publications.repository.publication_object_repository import PublicationObjectRepository
from app.extensions.publications.repository.publication_storage_file_repository import PublicationStorageFileRepository
from app.extensions.publications.repository.publication_version_attachment_repository import (
    PublicationVersionAttachmentRepository,
)
from app.extensions.publications.repository.publication_version_repository import PublicationVersionRepository
from app.extensions.publications.repository.publication_zip_repository import PublicationZipRepository
from app.extensions.publications.services.act_defaults_provider import ActDefaultsProvider
from app.extensions.publications.services.act_frbr_provider import ActFrbrProvider
from app.extensions.publications.services.act_package.act_package_builder_factory import ActPackageBuilderFactory
from app.extensions.publications.services.act_package.act_publication_data_provider import ActPublicationDataProvider
from app.extensions.publications.services.act_package.api_act_input_data_patcher_factory import (
    ApiActInputDataPatcherFactory,
)
from app.extensions.publications.services.act_package.documents_provider import PublicationDocumentsProvider
from app.extensions.publications.services.act_package.werkingsgebieden_provider import (
    PublicationWerkingsgebiedenProvider,
)
from app.extensions.publications.services.announcement_package.announcement_package_builder_factory import (
    AnnouncementPackageBuilderFactory,
)
from app.extensions.publications.services.assets.asset_remove_transparency import AssetRemoveTransparency
from app.extensions.publications.services.assets.publication_asset_provider import PublicationAssetProvider
from app.extensions.publications.services.bill_frbr_provider import BillFrbrProvider
from app.extensions.publications.services.doc_frbr_provider import DocFrbrProvider
from app.extensions.publications.services.pdf_export_service import PdfExportService
from app.extensions.publications.services.publication_announcement_defaults_provider import (
    PublicationAnnouncementDefaultsProvider,
)
from app.extensions.publications.services.publication_version_defaults_provider import (
    PublicationVersionDefaultsProvider,
)
from app.extensions.publications.services.publication_version_validator import PublicationVersionValidator
from app.extensions.publications.services.purpose_provider import PurposeProvider
from app.extensions.publications.services.state.patch_act_mutation_factory import PatchActMutationFactory
from app.extensions.publications.services.state.state_loader import StateLoader
from app.extensions.publications.services.state.state_version_factory import StateVersionFactory
from app.extensions.publications.services.state.versions.v1.state_v1 import StateV1
from app.extensions.publications.services.state.versions.v2.state_v2 import StateV2
from app.extensions.publications.services.state.versions.v2.state_v2_upgrader import StateV2Upgrader
from app.extensions.publications.services.state.versions.v3.state_v3 import StateV3
from app.extensions.publications.services.state.versions.v3.state_v3_upgrader import StateV3Upgrader
from app.extensions.publications.services.template_parser import TemplateParser
from app.extensions.publications.tables import PublicationActPackageTable, PublicationTemplateTable
from app.extensions.publications.tables.tables import (
    PublicationActPackageReportTable,
    PublicationActTable,
    PublicationAnnouncementPackageReportTable,
    PublicationAnnouncementPackageTable,
    PublicationAnnouncementTable,
    PublicationAreaOfJurisdictionTable,
    PublicationEnvironmentTable,
    PublicationPackageZipTable,
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


def depends_publication_act_repository(db: Session = Depends(depends_db)) -> PublicationActRepository:
    return PublicationActRepository(db)


def depends_publication_act(
    act_uuid: uuid.UUID,
    repository: PublicationActRepository = Depends(depends_publication_act_repository),
) -> PublicationActTable:
    maybe_act: Optional[PublicationActTable] = repository.get_by_uuid(act_uuid)
    if not maybe_act:
        raise HTTPException(status_code=404, detail="Publicatie regeling niet gevonden")
    return maybe_act


def depends_publication_act_active(
    act: PublicationActTable = Depends(depends_publication_act),
) -> PublicationActTable:
    if not act.Is_Active:
        raise HTTPException(status_code=404, detail="Publicatie regeling is gesloten")
    return act


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


def depends_publication_act_version_repository(db: Session = Depends(depends_db)) -> PublicationActVersionRepository:
    return PublicationActVersionRepository(db)


def depends_publication_act_package_repository(db: Session = Depends(depends_db)) -> PublicationActPackageRepository:
    return PublicationActPackageRepository(db)


def depends_publication_act_package(
    act_package_uuid: uuid.UUID,
    package_repository: PublicationActPackageRepository = Depends(depends_publication_act_package_repository),
) -> PublicationActPackageTable:
    package: Optional[PublicationActPackageTable] = package_repository.get_by_uuid(act_package_uuid)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


def depends_publication_zip_repository(db: Session = Depends(depends_db)) -> PublicationZipRepository:
    return PublicationZipRepository(db)


def depends_publication_zip(
    zip_uuid: uuid.UUID,
    repository: PublicationZipRepository = Depends(depends_publication_zip_repository),
) -> PublicationPackageZipTable:
    package_zip: Optional[PublicationPackageZipTable] = repository.get_by_uuid(zip_uuid)
    if package_zip is None:
        raise HTTPException(status_code=404, detail="Zip not found")
    return package_zip


def depends_publication_zip_by_act_package(
    act_package_uuid: uuid.UUID,
    repository: PublicationZipRepository = Depends(depends_publication_zip_repository),
) -> PublicationPackageZipTable:
    package_zip: Optional[PublicationPackageZipTable] = repository.get_by_act_package_uuid(act_package_uuid)
    if package_zip is None:
        raise HTTPException(status_code=404, detail="Package Zip not found")
    return package_zip


def depends_publication_act_report_repository(db: Session = Depends(depends_db)) -> PublicationActReportRepository:
    return PublicationActReportRepository(db)


def depends_publication_act_report(
    act_report_uuid: uuid.UUID,
    repository: PublicationActReportRepository = Depends(depends_publication_act_report_repository),
) -> PublicationActPackageReportTable:
    report: Optional[PublicationActPackageReportTable] = repository.get_by_uuid(act_report_uuid)
    if report is None:
        raise HTTPException(status_code=404, detail="Package report not found")
    return report


def depends_act_defaults_provider(
    main_config: dict = Depends(depends_main_config),
) -> ActDefaultsProvider:
    defaults: dict = main_config["publication"]["act_defaults"]
    return ActDefaultsProvider(defaults)


def depends_publication_version_defaults_provider(
    main_config: dict = Depends(depends_main_config),
) -> PublicationVersionDefaultsProvider:
    defaults: dict = main_config["publication"]["bill_defaults"]
    return PublicationVersionDefaultsProvider(defaults)


def depends_publication_announcement_defaults_provider(
    main_config: dict = Depends(depends_main_config),
) -> PublicationAnnouncementDefaultsProvider:
    defaults: dict = main_config["publication"]["announcement_defaults"]
    return PublicationAnnouncementDefaultsProvider(defaults)


def depends_publication_object_repository(
    db: Session = Depends(depends_db),
) -> PublicationObjectRepository:
    return PublicationObjectRepository(db)


def depends_bill_frbr_provider(
    db: Session = Depends(depends_db),
) -> BillFrbrProvider:
    return BillFrbrProvider(db)


def depends_act_frbr_provider(
    db: Session = Depends(depends_db),
) -> ActFrbrProvider:
    return ActFrbrProvider(db)


def depends_doc_frbr_provider(
    db: Session = Depends(depends_db),
) -> DocFrbrProvider:
    return DocFrbrProvider(db)


def depends_purpose_provider(
    db: Session = Depends(depends_db),
) -> PurposeProvider:
    return PurposeProvider(db)


def depends_publication_asset_provider(
    asset_repository: AssetRepository = Depends(depends_asset_repository),
) -> PublicationAssetProvider:
    return PublicationAssetProvider(
        asset_repository,
        AssetRemoveTransparency(),
    )


def depends_publication_werkingsgebieden_provider(
    area_repository: AreaGeometryRepository = Depends(depends_area_repository),
) -> PublicationWerkingsgebiedenProvider:
    return PublicationWerkingsgebiedenProvider(
        area_repository,
    )


def depends_publication_documents_provider(
    storage_file_repository: StorageFileRepository = Depends(depends_storage_file_repository),
) -> PublicationDocumentsProvider:
    return PublicationDocumentsProvider(
        storage_file_repository,
    )


def depends_act_publication_data_provider(
    publication_object_repository: PublicationObjectRepository = Depends(depends_publication_object_repository),
    publication_asset_provider: PublicationAssetProvider = Depends(depends_publication_asset_provider),
    publication_werkingsgebieden_provider: PublicationWerkingsgebiedenProvider = Depends(
        depends_publication_werkingsgebieden_provider
    ),
    publication_documents_provider: PublicationDocumentsProvider = Depends(depends_publication_documents_provider),
    publication_aoj_repository: PublicationAOJRepository = Depends(depends_publication_aoj_repository),
) -> ActPublicationDataProvider:
    return ActPublicationDataProvider(
        publication_object_repository,
        publication_asset_provider,
        publication_werkingsgebieden_provider,
        publication_documents_provider,
        publication_aoj_repository,
        TemplateParser(),
    )


def depends_state_v2_upgrader(
    act_version_repository: PublicationActVersionRepository = Depends(depends_publication_act_version_repository),
    act_package_repository: PublicationActPackageRepository = Depends(depends_publication_act_package_repository),
    act_data_provider: ActPublicationDataProvider = Depends(depends_act_publication_data_provider),
) -> StateV2Upgrader:
    return StateV2Upgrader(
        act_version_repository,
        act_package_repository,
        act_data_provider,
    )


def depends_state_v3_upgrader() -> StateV3Upgrader:
    return StateV3Upgrader()


def depends_state_version_factory(
    state_v2_upgrader: StateV2Upgrader = Depends(depends_state_v2_upgrader),
    state_v3_upgrader: StateV3Upgrader = Depends(depends_state_v3_upgrader),
) -> StateVersionFactory:
    factory: StateVersionFactory = StateVersionFactory(
        versions=[
            StateV1,
            StateV2,
            StateV3,
        ],
        upgraders=[
            state_v2_upgrader,
            state_v3_upgrader,
        ],
    )
    return factory


def depends_state_loader(
    version_factory: StateVersionFactory = Depends(depends_state_version_factory),
) -> StateLoader:
    state_loader: StateLoader = StateLoader(version_factory)
    return state_loader


def depends_patch_act_mutation_factory(
    asset_provider: PublicationAssetProvider = Depends(depends_publication_asset_provider),
) -> PatchActMutationFactory:
    return PatchActMutationFactory(
        asset_provider,
    )


def depends_api_act_input_data_patcher_factory(
    mutation_factory: PatchActMutationFactory = Depends(depends_patch_act_mutation_factory),
) -> ApiActInputDataPatcherFactory:
    return ApiActInputDataPatcherFactory(
        mutation_factory,
    )


def depends_act_package_builder_factory(
    db: Session = Depends(depends_db),
    settings: DynamicSettings = Depends(depends_settings),
    bill_frbr_provider: BillFrbrProvider = Depends(depends_bill_frbr_provider),
    act_frbr_provider: ActFrbrProvider = Depends(depends_act_frbr_provider),
    purpose_provider: PurposeProvider = Depends(depends_purpose_provider),
    state_loader: StateLoader = Depends(depends_state_loader),
    publication_data_provider: ActPublicationDataProvider = Depends(depends_act_publication_data_provider),
    data_patcher_factory: ApiActInputDataPatcherFactory = Depends(depends_api_act_input_data_patcher_factory),
) -> ActPackageBuilderFactory:
    return ActPackageBuilderFactory(
        db,
        settings,
        bill_frbr_provider,
        act_frbr_provider,
        purpose_provider,
        state_loader,
        publication_data_provider,
        data_patcher_factory,
    )


def depends_publication_announcement_repository(db: Session = Depends(depends_db)) -> PublicationAnnouncementRepository:
    return PublicationAnnouncementRepository(db)


def depends_publication_announcement(
    announcement_uuid: uuid.UUID,
    repository: PublicationAnnouncementRepository = Depends(depends_publication_announcement_repository),
) -> PublicationAnnouncementTable:
    maybe_announcement: Optional[PublicationAnnouncementTable] = repository.get_by_uuid(announcement_uuid)
    if not maybe_announcement:
        raise HTTPException(status_code=404, detail="Publication announcement niet gevonden")
    return maybe_announcement


def depends_announcement_package_builder_factory(
    db: Session = Depends(depends_db),
    doc_frbr_provider: DocFrbrProvider = Depends(depends_doc_frbr_provider),
    state_loader: StateLoader = Depends(depends_state_loader),
) -> AnnouncementPackageBuilderFactory:
    return AnnouncementPackageBuilderFactory(
        db,
        doc_frbr_provider,
        state_loader,
    )


def depends_publication_zip_by_announcement_package(
    announcement_package_uuid: uuid.UUID,
    repository: PublicationZipRepository = Depends(depends_publication_zip_repository),
) -> PublicationPackageZipTable:
    package_zip: Optional[PublicationPackageZipTable] = repository.get_by_announcement_package_uuid(
        announcement_package_uuid
    )
    if package_zip is None:
        raise HTTPException(status_code=404, detail="Package Zip not found")
    return package_zip


def depends_publication_announcement_report_repository(
    db: Session = Depends(depends_db),
) -> PublicationAnnouncementReportRepository:
    return PublicationAnnouncementReportRepository(db)


def depends_publication_announcement_report(
    announcement_report_uuid: uuid.UUID,
    repository: PublicationAnnouncementReportRepository = Depends(depends_publication_announcement_report_repository),
) -> PublicationAnnouncementPackageReportTable:
    report: Optional[PublicationAnnouncementPackageReportTable] = repository.get_by_uuid(announcement_report_uuid)
    if report is None:
        raise HTTPException(status_code=404, detail="Package report not found")
    return report


def depends_publication_announcement_package_repository(
    db: Session = Depends(depends_db),
) -> PublicationAnnouncementPackageRepository:
    return PublicationAnnouncementPackageRepository(db)


def depends_publication_announcement_package(
    announcement_package_uuid: uuid.UUID,
    package_repository: PublicationAnnouncementPackageRepository = Depends(
        depends_publication_announcement_package_repository
    ),
) -> PublicationAnnouncementPackageTable:
    package: Optional[PublicationAnnouncementPackageTable] = package_repository.get_by_uuid(announcement_package_uuid)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


def depends_publication_storage_file_repository(
    db: Session = Depends(depends_db),
) -> PublicationStorageFileRepository:
    return PublicationStorageFileRepository(db)


def depends_publication_version_attachment_repository(
    db: Session = Depends(depends_db),
) -> PublicationVersionAttachmentRepository:
    return PublicationVersionAttachmentRepository(db)


def depends_publication_version_validator() -> PublicationVersionValidator:
    return PublicationVersionValidator()


def depends_pdf_export_service(
    settings: DynamicSettings = Depends(depends_settings),
) -> PdfExportService:
    return PdfExportService(settings)
