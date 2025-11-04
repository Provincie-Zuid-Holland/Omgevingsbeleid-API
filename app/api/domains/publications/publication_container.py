from dependency_injector import containers, providers

import app.api.domains.publications.repository as repositories
import app.api.domains.publications.services as services
import app.api.domains.publications.services.act_package as act_package_services
import app.api.domains.publications.services.announcement_package as announcement_package_services
import app.api.domains.publications.services.assets as assets_services
import app.api.domains.publications.services.assets as publication_asset_services
import app.api.domains.publications.services.state as state_services
import app.api.domains.publications.services.state.versions as state_versions


class PublicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    main_config = providers.Dependency()
    area_repository = providers.Dependency()
    area_geometry_repository = providers.Dependency()
    asset_repository = providers.Dependency()
    object_field_mapping_provider = providers.Dependency()

    act_package_repository = providers.Singleton(repositories.PublicationActPackageRepository)
    act_report_repository = providers.Singleton(repositories.PublicationActReportRepository)
    act_repository = providers.Singleton(repositories.PublicationActRepository)
    act_version_repository = providers.Singleton(repositories.PublicationActVersionRepository)
    announcement_package_repository = providers.Singleton(repositories.PublicationAnnouncementPackageRepository)
    announcement_report_repository = providers.Singleton(repositories.PublicationAnnouncementReportRepository)
    announcement_repository = providers.Singleton(repositories.PublicationAnnouncementRepository)
    aoj_repository = providers.Singleton(repositories.PublicationAOJRepository)
    environment_repository = providers.Singleton(repositories.PublicationEnvironmentRepository)
    object_repository = providers.Singleton(repositories.PublicationObjectRepository)
    publication_repository = providers.Singleton(repositories.PublicationRepository)
    storage_file_repository = providers.Singleton(repositories.PublicationStorageFileRepository)
    template_repository = providers.Singleton(repositories.PublicationTemplateRepository)
    version_attachment_repository = providers.Singleton(repositories.PublicationVersionAttachmentRepository)
    version_repository = providers.Singleton(repositories.PublicationVersionRepository)
    zip_repository = providers.Singleton(repositories.PublicationZipRepository)

    act_defaults_provider = providers.Factory(
        services.ActDefaultsProvider,
        main_config=main_config,
    )
    act_frbr_provider = providers.Singleton(services.ActFrbrProvider)
    bill_frbr_provider = providers.Singleton(services.BillFrbrProvider)
    doc_frbr_provider = providers.Singleton(services.DocFrbrProvider)
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
    purpose_provider = providers.Singleton(services.PurposeProvider)
    template_parser = providers.Singleton(services.TemplateParser)

    documents_provider = providers.Singleton(
        act_package_services.PublicationDocumentsProvider,
        file_repostiory=storage_file_repository,
    )
    werkingsgebieden_provider = providers.Singleton(
        act_package_services.PublicationWerkingsgebiedenProvider,
        area_repository=area_repository,
    )

    publication_object_provider = providers.Factory(
        services.PublicationObjectProvider,
        publication_object_repository=object_repository,
        object_field_mapping_provider=object_field_mapping_provider,
    )

    unified_packages_provider = providers.Singleton(services.UnifiedPackagesProvider)

    asset_remove_transparency = providers.Singleton(assets_services.AssetRemoveTransparency)

    publication_asset_provider = providers.Singleton(
        publication_asset_services.PublicationAssetProvider,
        asset_repository=asset_repository,
        asset_remove_transparency=asset_remove_transparency,
    )

    patch_act_mutation_factory = providers.Singleton(
        state_services.PatchActMutationFactory,
        asset_provider=publication_asset_provider,
    )
    api_act_input_data_patcher_factory = providers.Singleton(
        act_package_services.ApiActInputDataPatcherFactory,
        mutation_factory=patch_act_mutation_factory,
    )
    dso_act_input_data_builder_factory = providers.Singleton(
        act_package_services.DsoActInputDataBuilderFactory,
        koop_settings=config.PUBLICATION_KOOP.provided,
        ow_dataset=config.PUBLICATION_OW_DATASET,
        ow_gebied=config.PUBLICATION_OW_GEBIED,
    )
    act_publication_data_provider = providers.Factory(
        act_package_services.ActPublicationDataProvider,
        publication_object_provider=publication_object_provider,
        publication_asset_provider=publication_asset_provider,
        publication_werkingsgebieden_provider=werkingsgebieden_provider,
        publication_documents_provider=documents_provider,
        publication_aoj_repository=aoj_repository,
        template_parser=template_parser,
    )

    state_version_factory = providers.Factory(
        state_services.StateVersionFactory,
        versions=[
            state_versions.StateV1,
            state_versions.StateV2,
            state_versions.StateV3,
            state_versions.StateV4,
            state_versions.StateV5,
        ],
        upgraders=providers.List(
            providers.Factory(
                state_versions.StateV2Upgrader,
                act_version_repository=act_version_repository,
                act_package_repository=act_package_repository,
                act_data_provider=act_publication_data_provider,
            ),
            providers.Factory(state_versions.StateV3Upgrader),
            providers.Factory(state_versions.StateV4Upgrader),
            providers.Factory(state_versions.StateV5Upgrader),
        ),
    )
    state_loader = providers.Singleton(
        state_services.StateLoader,
        state_version_factory=state_version_factory,
    )

    act_package_builder_factory = providers.Singleton(
        act_package_services.ActPackageBuilderFactory,
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
        doc_frbr_provider=doc_frbr_provider,
        state_loader=state_loader,
    )
