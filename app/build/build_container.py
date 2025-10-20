from dependency_injector import containers, providers

from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.build import api_builder
import app.build.endpoint_builders.objects as endpoint_builders_objects
import app.build.endpoint_builders.modules as endpoint_builders_modules
import app.build.endpoint_builders.users as endpoint_builders_users
import app.build.endpoint_builders.others as endpoint_builders_others
import app.build.endpoint_builders.werkingsgebieden as endpoint_builders_werkingsgebieden
import app.build.endpoint_builders.publications as endpoint_builders_publications
from app.build.endpoint_builders import endpoint_builder_provider
from app.build.services import (
    config_parser,
    object_intermediate_builder,
    tables_builder,
    validator_provider,
    object_models_builder,
)
import app.build.services.validators.validators as validators
from app.build.services.model_dynamic_type_builder import ModelDynamicTypeBuilder
from app.core.db.session import create_db_engine
from app.core.services import MainConfig, ModelsProvider
from app.core.services.event import event_manager
from app.core.settings import Settings
from sqlalchemy.orm import sessionmaker
from app.build.events import create_model_event_listeners, generate_table_event_listeners


class BuildContainer(containers.DeclarativeContainer):
    config = providers.Configuration(pydantic_settings=[Settings()])

    db_engine = providers.Singleton(
        create_db_engine,
        uri=config.SQLALCHEMY_DATABASE_URI,
        echo=config.SQLALCHEMY_ECHO,
    )
    db_session_factory = providers.Singleton(
        sessionmaker,
        bind=db_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    object_static_repository = providers.Singleton(ObjectStaticRepository)

    validator_provider = providers.Singleton(
        validator_provider.ValidatorProvider,
        validators=providers.List(
            providers.Factory(validators.NoneToDefaultValueValidator),
            providers.Factory(validators.LengthValidator),
            providers.Factory(validators.PlainTextValidator),
            providers.Factory(validators.FilenameValidator),
            providers.Factory(validators.HtmlValidator),
            providers.Factory(validators.ImageValidator),
            providers.Factory(validators.NotEqualRootValidator),
            providers.Factory(
                validators.ObjectCodeExistsValidator,
                session_factory=db_session_factory,
                object_static_repository=object_static_repository,
            ),
            providers.Factory(validators.ObjectCodeAllowedTypeValidator),
            providers.Factory(
                validators.ObjectCodesExistsValidator,
                session_factory=db_session_factory,
                object_static_repository=object_static_repository,
            ),
            providers.Factory(validators.ObjectCodesAllowedTypeValidator),
        ),
    )

    build_event_listeners = providers.Factory(
        event_manager.EventListeners,
        listeners=providers.List(
            # GenerateTableEvent
            providers.Factory(generate_table_event_listeners.AddObjectCodeRelationshipListener),
            providers.Factory(generate_table_event_listeners.AddAreasRelationshipListener),
            providers.Factory(generate_table_event_listeners.AddUserRelationshipListener),
            providers.Factory(generate_table_event_listeners.AddWerkingsgebiedenRelationshipListener),
            providers.Factory(generate_table_event_listeners.AddStoreageFileRelationshipListener),
            # CreateModelEvent
            providers.Factory(create_model_event_listeners.ObjectsExtenderListener),
            providers.Factory(create_model_event_listeners.ObjectStaticsExtenderListener),
            providers.Factory(create_model_event_listeners.AddRelationsListener),
            providers.Factory(create_model_event_listeners.JoinWerkingsgebiedenListener),
            providers.Factory(create_model_event_listeners.AddJoinDocumentsToObjectModelListener),
            providers.Factory(create_model_event_listeners.AddPublicRevisionsToObjectModelListener),
            providers.Factory(create_model_event_listeners.AddNextObjectVersionToObjectModelListener),
            providers.Factory(create_model_event_listeners.AddRelatedObjectsToWerkingsgebiedObjectModelListener),
        ),
    )
    build_event_manager = providers.Singleton(
        event_manager.EventManager,
        event_listeners=build_event_listeners,
    )

    models_provider = providers.Singleton(ModelsProvider)
    model_dynamic_type_builder = providers.Singleton(
        ModelDynamicTypeBuilder,
        models_provider=models_provider,
    )

    endpoint_builder_provider = providers.Singleton(
        endpoint_builder_provider.EndpointBuilderProvider,
        endpoint_builders=providers.List(
            # fmt: off
            # Objects domain
            providers.Factory(endpoint_builders_objects.ObjectLatestEndpointBuilder),
            providers.Factory(endpoint_builders_objects.ObjectVersionEndpointBuilder),
            providers.Factory(endpoint_builders_objects.ObjectCountsEndpointBuilder),
            providers.Factory(endpoint_builders_objects.ObjectListValidLineagesEndpointBuilder),
            providers.Factory(endpoint_builders_objects.ObjectListValidLineageTreeEndpointBuilder),
            providers.Factory(endpoint_builders_objects.ObjectListAllLatestEndpointBuilder),
            providers.Factory(endpoint_builders_objects.EditObjectStaticEndpointBuilder),
            providers.Factory(endpoint_builders_objects.AtemporalCreateObjectEndpointBuilder),
            providers.Factory(endpoint_builders_objects.AtemporalEditObjectEndpointBuilder),
            providers.Factory(endpoint_builders_objects.AtemporalDeleteObjectEndpointBuilder),
            providers.Factory(endpoint_builders_objects.AcknowledgedRelationEditEndpointBuilder),
            providers.Factory(endpoint_builders_objects.AcknowledgedRelationListEndpointBuilder),
            providers.Factory(endpoint_builders_objects.AcknowledgedRelationRequestEndpointBuilder),
            providers.Factory(endpoint_builders_objects.RelationsListEndpointBuilder),
            providers.Factory(endpoint_builders_objects.RelationsOverwriteEndpointBuilder),
            providers.Factory(endpoint_builders_objects.SearchObjectsEndpointBuilder),
            # Publications domain
            #   Acts
            providers.Factory(endpoint_builders_publications.acts.ClosePublicationActEndpointBuilder),
            providers.Factory(endpoint_builders_publications.acts.CreateActEndpointBuilder),
            providers.Factory(endpoint_builders_publications.acts.DetailActEndpointBuilder),
            providers.Factory(endpoint_builders_publications.acts.EditPublicationActEndpointBuilder),
            providers.Factory(endpoint_builders_publications.acts.ListPublicationActsEndpointBuilder),
            #   Area of jurisdictions
            providers.Factory(endpoint_builders_publications.area_of_jurisdictions.CreatePublicationAOJEndpointBuilder),
            providers.Factory(endpoint_builders_publications.area_of_jurisdictions.ListPublicationAOJEndpointBuilder),
            #   DSO values
            providers.Factory(endpoint_builders_publications.dso_values.ListAreaDesignationGroupsEndpointBuilder),
            providers.Factory(endpoint_builders_publications.dso_values.ListAreaDesignationTypesEndpointBuilder),
            #   Templates
            providers.Factory(endpoint_builders_publications.templates.CreatePublicationTemplateEndpointBuilder),
            providers.Factory(endpoint_builders_publications.templates.DetailPublicationTemplateEndpointBuilder),
            providers.Factory(endpoint_builders_publications.templates.EditPublicationTemplateEndpointBuilder),
            providers.Factory(endpoint_builders_publications.templates.ListPublicationTemplatesEndpointBuilder),
            #   Environments
            providers.Factory(endpoint_builders_publications.environments.CreatePublicationEnvironmentEndpointBuilder),
            providers.Factory(endpoint_builders_publications.environments.DetailPublicationEnvironmentEndpointBuilder),
            providers.Factory(endpoint_builders_publications.environments.EditPublicationEnvironmentEndpointBuilder),
            providers.Factory(endpoint_builders_publications.environments.ListPublicationEnvironmentsEndpointBuilder),
            #   Publications
            #       Act Packages
            providers.Factory(
                endpoint_builders_publications.publications.act_packages.CreatePublicationPackageEndpointBuilder
            ),
            providers.Factory(endpoint_builders_publications.publications.act_packages.DetailActPackageEndpointBuilder),
            providers.Factory(endpoint_builders_publications.publications.act_packages.DownloadPackageEndpointBuilder),
            providers.Factory(
                endpoint_builders_publications.publications.act_packages.ListPublicationPackagesEndpointBuilder
            ),
            #       Act Reports
            providers.Factory(
                endpoint_builders_publications.publications.act_reports.DetailActPackageReportEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.act_reports.DownloadActPackageReportEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.act_reports.ListActPackageReportsEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.act_reports.UploadActPackageReportEndpointBuilder
            ),
            #       Announcement Packages
            providers.Factory(
                endpoint_builders_publications.publications.announcement_packages.CreatePublicationAnnouncementPackageEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.announcement_packages.DetailAnnouncementPackageEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.announcement_packages.DownloadPublicationAnnouncementPackageEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.announcement_packages.ListPublicationAnnouncementPackagesEndpointBuilder
            ),
            #       Unified Packages
            providers.Factory(endpoint_builders_publications.packages.ListUnifiedPackagesEndpointBuilder),
            #       Announcement Reports
            providers.Factory(
                endpoint_builders_publications.publications.announcement_reports.DetailAnnouncementPackageReportEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.announcement_reports.DownloadAnnouncementPackageReportEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.announcement_reports.ListAnnouncementPackageReportsEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.announcement_reports.UploadAnnouncementPackageReportEndpointBuilder
            ),
            #       Announcement
            providers.Factory(
                endpoint_builders_publications.publications.announcements.CreatePublicationAnnouncementEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.announcements.DetailPublicationAnnouncementEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.announcements.EditPublicationAnnouncementEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.announcements.ListPublicationAnnouncementsEndpointBuilder
            ),
            #       Publications
            providers.Factory(endpoint_builders_publications.publications.CreatePublicationEndpointBuilder),
            providers.Factory(endpoint_builders_publications.publications.DetailPublicationEndpointBuilder),
            providers.Factory(endpoint_builders_publications.publications.EditPublicationEndpointBuilder),
            providers.Factory(endpoint_builders_publications.publications.ListPublicationsEndpointBuilder),
            #       Versions
            providers.Factory(
                endpoint_builders_publications.publications.versions.CreatePublicationVersionPdfEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.versions.CreatePublicationVersionEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.versions.DeletePublicationVersionEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.versions.DetailPublicationVersionEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.versions.EditPublicationVersionEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.versions.ListPublicationVersionsEndpointBuilder
            ),
            #           Attachments
            providers.Factory(
                endpoint_builders_publications.publications.versions.attachments.DeletePublicationVersionAttachmentEndpointBuilder
            ),
            providers.Factory(
                endpoint_builders_publications.publications.versions.attachments.UploadPublicationVersionAttachmentEndpointBuilder
            ),
            # Users domain
            providers.Factory(endpoint_builders_users.AuthLoginAccessTokenEndpointBuilder),
            providers.Factory(endpoint_builders_users.AuthResetPasswordEndpointBuilder),
            providers.Factory(endpoint_builders_users.CreateUserEndpointBuilder),
            providers.Factory(endpoint_builders_users.EditUserEndpointBuilder),
            providers.Factory(endpoint_builders_users.GetUserEndpointBuilder),
            providers.Factory(endpoint_builders_users.ListUsersEndpointBuilder),
            providers.Factory(endpoint_builders_users.ResetUserPasswordEndpointBuilder),
            providers.Factory(endpoint_builders_users.SearchUsersEndpointBuilder),
            # Module domain
            providers.Factory(endpoint_builders_modules.ActivateModuleEndpointBuilder),
            providers.Factory(endpoint_builders_modules.CloseModuleEndpointBuilder),
            providers.Factory(endpoint_builders_modules.CompleteModuleEndpointBuilder),
            providers.Factory(endpoint_builders_modules.CreateModuleEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleValidateEndpointBuilder),
            providers.Factory(endpoint_builders_modules.EditModuleEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ListActiveModuleObjectsEndpointBuilder),
            providers.Factory(
                endpoint_builders_modules.ListModuleObjectsEndpointBuilder,
                model_dynamic_type_enricher=model_dynamic_type_builder,
            ),
            providers.Factory(endpoint_builders_modules.ListModulesEndpointResolverBuilder),
            providers.Factory(endpoint_builders_modules.ModuleAddExistingObjectEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleAddNewObjectEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleEditObjectContextEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleGetObjectContextEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleListLineageTreeEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleListStatusesEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleObjectLatestEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleObjectVersionEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleOverviewEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModulePatchObjectEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModulePatchStatusEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleRemoveObjectEndpointBuilder),
            providers.Factory(endpoint_builders_modules.ModuleSnapshotEndpointBuilder),
            providers.Factory(endpoint_builders_modules.PublicListModulesEndpointBuilder),
            providers.Factory(endpoint_builders_modules.PublicModuleOverviewEndpointBuilder),
            # Werkingsgebieden domain
            providers.Factory(endpoint_builders_werkingsgebieden.ListObjectsByAreasEndpointBuilder),
            providers.Factory(endpoint_builders_werkingsgebieden.ListObjectsByGeometryEndpointBuilder),
            providers.Factory(endpoint_builders_werkingsgebieden.ListWerkingsgebiedenEndpointBuilder),
            # Others
            providers.Factory(endpoint_builders_others.ListStorageFilesEndpointBuilder),
            providers.Factory(endpoint_builders_others.DetailStorageFilesEndpointBuilder),
            providers.Factory(endpoint_builders_others.DownloadStorageFilesEndpointBuilder),
            providers.Factory(endpoint_builders_others.StorageFileUploadFileEndpointBuilder),
            providers.Factory(endpoint_builders_others.FullGraphEndpointBuilder),
            providers.Factory(endpoint_builders_others.ObjectGraphEndpointBuilder),
            providers.Factory(endpoint_builders_others.MssqlSearchEndpointBuilder),
            providers.Factory(endpoint_builders_others.MssqlValidSearchEndpointBuilder),
            # fmt: on
        ),
    )

    object_intermediate_builder = providers.Factory(
        object_intermediate_builder.ObjectIntermediateBuilder,
        validator_provider=validator_provider,
    )
    object_models_builder = providers.Factory(
        object_models_builder.ObjectModelsBuilder,
        validator_provider=validator_provider,
        event_manager=build_event_manager,
    )

    main_config = providers.Singleton(MainConfig, config.MAIN_CONFIG_FILE)
    config_parser = providers.Factory(
        config_parser.ConfigParser,
        main_config=main_config,
        object_config_path=config.OBJECT_CONFIG_PATH,
        object_intermediate_builder=object_intermediate_builder,
    )

    tables_builder = providers.Factory(
        tables_builder.TablesBuilder,
        event_manager=build_event_manager,
    )

    api_builder = providers.Factory(
        api_builder.ApiBuilder,
        config_parser=config_parser,
        object_models_builder=object_models_builder,
        tables_builder=tables_builder,
        endpoint_builder_provider=endpoint_builder_provider,
        models_provider=models_provider,
    )
