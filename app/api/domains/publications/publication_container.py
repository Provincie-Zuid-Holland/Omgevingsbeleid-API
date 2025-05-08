from dependency_injector import containers, providers

import app.api.domains.publications.repository as repositories
import app.api.domains.publications.services as services
import app.api.domains.publications.services.act_package as act_package_services
import app.api.domains.publications.services.announcement_package as announcement_package_services
import app.api.domains.publications.services.assets as assets_services
import app.api.domains.publications.services.state as state_services
import app.api.domains.publications.services.state.versions as state_versions
from app.api.domains.publications.services.assets import publication_asset_provider


class PublicationContainer(containers.DeclarativeContainer):
    config = providers.Dependency()
    db = providers.Dependency()
    main_config = providers.Dependency()
    area_geometry_repository = providers.Dependency()
    storage_file_repository = providers.Dependency()
    asset_repository = providers.Dependency()

    act_package_repository = providers.Singleton(repositories.PublicationActPackageRepository, db=db)
    act_report_repository = providers.Singleton(
        repositories.PublicationActReportRepository,
        db=db,
    )
    act_repository = providers.Singleton(
        repositories.PublicationActRepository,
        db=db,
    )
    act_version_repository = providers.Singleton(
        repositories.PublicationActVersionRepository,
        db=db,
    )
    announcement_package_repository = providers.Singleton(repositories.PublicationAnnouncementPackageRepository, db=db)
    announcement_report_repository = providers.Singleton(repositories.PublicationAnnouncementReportRepository, db=db)
    announcement_repository = providers.Singleton(repositories.PublicationAnnouncementRepository, db=db)
    aoj_repository = providers.Singleton(repositories.PublicationAOJRepository, db=db)
    environment_repository = providers.Singleton(repositories.PublicationEnvironmentRepository, db=db)
    object_repository = providers.Singleton(repositories.PublicationObjectRepository, db=db)
    publication_repository = providers.Singleton(repositories.PublicationRepository, db=db)
    storage_file_repository = providers.Singleton(repositories.PublicationStorageFileRepository, db=db)
    template_repository = providers.Singleton(repositories.PublicationTemplateRepository, db=db)
    version_attachment_repository = providers.Singleton(repositories.PublicationVersionAttachmentRepository, db=db)
    version_repository = providers.Singleton(repositories.PublicationVersionRepository, db=db)
    zip_repository = providers.Singleton(repositories.PublicationZipRepository, db=db)

    act_defaults_provider = providers.Factory(
        services.ActDefaultsProvider,
        main_config=main_config,
    )
    act_frbr_provider = providers.Singleton(
        services.ActFrbrProvider,
        db=db,
    )
    bill_frbr_provider = providers.Singleton(
        services.BillFrbrProvider,
        db=db,
    )
    doc_frbr_provider = providers.Singleton(
        services.DocFrbrProvider,
        db=db,
    )
    pdf_export_service = providers.Singleton(
        services.PdfExportService,
        koop_settings=config.PUBLICATION_KOOP,
    )
    announcement_defaults_provider = providers.Factory(
        services.PublicationAnnouncementDefaultsProvider,
        main_config=main_config,
    )
    version_defaults_provider = providers.Factory(
        services.PublicationVersionDefaultsProvider,
        main_config=main_config,
    )
    version_validator = providers.Singleton(services.PublicationVersionValidator)
    purpose_provider = providers.Singleton(db=db)
    template_parser = providers.Singleton(services.TemplateParser)

    documents_provider = providers.Singleton(
        act_package_services.PublicationDocumentsProvider,
        file_repostiory=storage_file_repository,
    )
    werkingsgebieden_provider = providers.Singleton(
        act_package_services.PublicationWerkingsgebiedenProvider,
        area_geometry_repository=area_geometry_repository,
    )

    asset_remove_transparency = providers.Singleton(assets_services.AssetRemoveTransparency)

    asset_provider = providers.Singleton(
        publication_asset_provider.PublicationAssetProvider,
        asset_repository=asset_repository,
        asset_remove_transparency=asset_remove_transparency,
    )

    state_version_factory = providers.Factory(
        state_services.StateVersionFactory,
        versions=[
            state_versions.StateV1,
            state_versions.StateV2,
            state_versions.StateV3,
            state_versions.StateV4,
        ],
        upgraders=providers.List(
            state_versions.StateV2Upgrader,
            state_versions.StateV3Upgrader,
            state_versions.StateV4Upgrader,
        ),
    )
    state_loader = providers.Singleton(
        state_services.StateLoader,
        state_version_factory=state_version_factory,
    )
    patch_act_mutation_factory = providers.Singleton(
        state_services.PatchActMutationFactory,
        asset_provider=asset_provider,
    )
    api_act_input_data_patcher_factory = providers.Singleton(
        act_package_services.ApiActInputDataPatcherFactory,
        mutation_factory=patch_act_mutation_factory,
    )
    dso_act_input_data_builder_factory = providers.Singleton(
        act_package_services.DsoActInputDataBuilderFactory,
        koop_settings=config.PUBLICATION_KOOP,
    )
    act_publication_data_provider = providers.Factory(
        act_package_services.ActPublicationDataProvider,
        publication_object_repository=object_repository,
        publication_asset_provider=asset_provider,
        publication_werkingsgebieden_provider=werkingsgebieden_provider,
        publication_documents_provider=documents_provider,
        publication_aoj_repository=aoj_repository,
        template_parser=template_parser,
    )
    act_package_builder_factory = providers.Singleton(
        act_package_services.ActPackageBuilderFactory,
        db=db,
        dso_builder_factory=dso_act_input_data_builder_factory,
        bill_frbr_provider=bill_frbr_provider,
        act_frbr_provider=act_frbr_provider,
        purpose_provider=purpose_provider,
        state_loader=state_loader,
        publication_data_provider=act_publication_data_provider,
        data_patcher_factory=api_act_input_data_patcher_factory,
    )
    announcement_package_builder_factory = providers.Singleton(
        announcement_package_services.AnnouncementPackageBuilderFactory,
        db=db,
        doc_frbr_provider=doc_frbr_provider,
        state_loader=state_loader,
    )
