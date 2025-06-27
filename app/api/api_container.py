from datetime import timedelta

from dependency_injector import containers, providers
from sqlalchemy.orm import sessionmaker

import app.api.domains.modules as module_domain
import app.api.domains.modules.services as module_services
import app.api.domains.objects.repositories as object_repositories
import app.api.domains.objects.services as object_services
import app.api.domains.users as user_domain
import app.api.domains.werkingsgebieden.repositories as werkingsgebieden_repositories
import app.api.domains.werkingsgebieden.services as werkingsgebied_services
import app.api.events.listeners as event_listeners
from app.api.domains.others.repositories import storage_file_repository
from app.api.domains.publications.publication_container import PublicationContainer
from app.api.services import permission_service
from app.core.db.session import create_db_engine, init_db_session
from app.core.services.event import event_manager
from app.core.services.main_config import MainConfig
from app.core.settings import Settings


class ApiContainer(containers.DeclarativeContainer):
    models_provider = providers.Dependency()

    config = providers.Configuration(pydantic_settings=[Settings()])
    main_config = providers.Singleton(MainConfig, config.MAIN_CONFIG_FILE)

    db_engine = providers.Singleton(
        create_db_engine,
        uri=config.SQLALCHEMY_DATABASE_URI,
        echo=config.SQLALCHEMY_ECHO,
    )
    db_session_factory = providers.Singleton(sessionmaker, bind=db_engine, autocommit=False, autoflush=False)
    db = providers.Resource(
        init_db_session,
        session_factory=db_session_factory,
    )

    permission_service = providers.Singleton(
        permission_service.PermissionService,
        main_config=main_config,
    )

    storage_file_repository = providers.Singleton(
        storage_file_repository.StorageFileRepository,
        db=db,
    )
    object_repository = providers.Singleton(object_repositories.ObjectRepository, db=db)
    object_static_repository = providers.Singleton(object_repositories.ObjectStaticRepository, db=db)
    asset_repository = providers.Singleton(object_repositories.AssetRepository, db=db)
    werkingsgebieden_repository = providers.Singleton(werkingsgebieden_repositories.WerkingsgebiedenRepository, db=db)
    sqlite_geometry_repository = providers.Singleton(werkingsgebieden_repositories.SqliteGeometryRepository, db=db)
    sqlite_area_geometry_repository = providers.Singleton(
        werkingsgebieden_repositories.SqliteAreaGeometryRepository,
        db=db,
    )
    mssql_geometry_repository = providers.Singleton(werkingsgebieden_repositories.MssqlGeometryRepository, db=db)
    mssql_area_geometry_repository = providers.Singleton(
        werkingsgebieden_repositories.MssqlAreaGeometryRepository, db=db
    )
    area_repository = providers.Singleton(werkingsgebieden_repositories.AreaRepository, db=db)
    module_object_context_repository = providers.Singleton(module_domain.ModuleObjectContextRepository, db=db)
    module_object_repository = providers.Singleton(module_domain.ModuleObjectRepository, db=db)
    module_repository = providers.Singleton(module_domain.ModuleRepository, db=db)
    module_status_repository = providers.Singleton(module_domain.ModuleStatusRepository, db=db)
    acknowledged_relations_repository = providers.Singleton(object_repositories.AcknowledgedRelationsRepository, db=db)

    geometry_repository = providers.Selector(
        config.DB_TYPE,
        sqlite=sqlite_geometry_repository,
        mssql=mssql_geometry_repository,
    )
    area_geometry_repository = providers.Selector(
        config.DB_TYPE,
        sqlite=sqlite_area_geometry_repository,
        mssql=mssql_area_geometry_repository,
    )

    html_images_extractor_factory = providers.Factory(
        event_listeners.HtmlImagesExtractorFactory,
        asset_repository=asset_repository,
        db=db,
    )
    image_inserter_factory = providers.Factory(
        event_listeners.ImageInserterFactory,
        asset_repository=asset_repository,
    )
    html_images_inserter_factory = providers.Factory(
        event_listeners.HtmlImagesInserterFactory,
        asset_repository=asset_repository,
    )
    store_images_extractor_factory = providers.Factory(
        event_listeners.StoreImagesExtractorFactory,
        asset_repository=asset_repository,
        db=db,
    )

    access_token_lifetime = providers.Selector(
        config.DEBUG_MODE_STR,
        yes=providers.Object(timedelta(days=5)),
        no=providers.Callable(timedelta, minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    security = providers.Factory(
        user_domain.Security,
        secret_key=config.SECRET_KEY,
        token_lifetime=access_token_lifetime,
    )
    user_repository = providers.Factory(
        user_domain.UserRepository,
        db=db,
        security=security,
    )

    add_relations_service_factory = providers.Singleton(
        object_services.AddRelationsServiceFactory,
        db=db,
    )
    join_werkingsgebieden_service_factory = providers.Singleton(
        werkingsgebied_services.JoinWerkingsgebiedenServiceFactory,
        db=db,
    )
    column_image_inserter_factory = providers.Singleton(
        object_services.ColumnImageInserterFactory,
        asset_repository=asset_repository,
    )
    add_public_revisions_service_factory = providers.Singleton(
        module_services.AddPublicRevisionsServiceFactory,
        db=db,
    )
    add_next_object_versions_service_factory = providers.Singleton(
        object_services.AddNextObjectVersionServiceFactory,
        db=db,
    )
    add_werkingsgebied_related_objects_service_factory = providers.Singleton(
        object_services.AddWerkingsgebiedRelatedObjectsServiceFactory,
        db=db,
    )

    object_provider = providers.Factory(
        module_services.ObjectProvider,
        object_repository=object_repository,
        module_object_repository=module_object_repository,
    )

    event_listeners = providers.Factory(
        event_manager.EventListeners,
        listeners=providers.List(
            # RetrievedObjectsEvent
            providers.Factory(
                event_listeners.AddRelationsToObjectsListener,
                relations_factory=add_relations_service_factory,
            ),
            providers.Factory(
                event_listeners.JoinWerkingsgebiedenToObjectsListener,
                service_factory=join_werkingsgebieden_service_factory,
            ),
            providers.Factory(
                event_listeners.InsertHtmlImagesForObjectListener,
                service_factory=html_images_inserter_factory,
            ),
            providers.Factory(
                event_listeners.GetColumnImagesForObjectListener,
                service_factory=column_image_inserter_factory,
            ),
            providers.Factory(
                event_listeners.GetImagesForObjectListener,
                service_factory=image_inserter_factory,
            ),
            providers.Factory(
                event_listeners.AddPublicRevisionsToObjectsListener,
                service_factory=add_public_revisions_service_factory,
            ),
            providers.Factory(
                event_listeners.AddNextObjectVersionToObjectsListener,
                service_factory=add_next_object_versions_service_factory,
            ),
            providers.Factory(
                event_listeners.AddWerkingsgebiedRelatedObjectsToObjectsListener,
                service_factory=add_werkingsgebied_related_objects_service_factory,
            ),
            # RetrievedModuleObjectsEvent
            providers.Factory(
                event_listeners.InsertHtmlImagesForModuleListener,
                service_factory=html_images_inserter_factory,
            ),
            providers.Factory(
                event_listeners.GetColumnImagesForModuleObjectListener,
                service_factory=column_image_inserter_factory,
            ),
            providers.Factory(
                event_listeners.JoinWerkingsgebiedToModuleObjectsListener,
                service_factory=join_werkingsgebieden_service_factory,
            ),
            providers.Factory(
                event_listeners.GetImagesForModuleListener,
                service_factory=image_inserter_factory,
            ),
            # BeforeSelectExecutionEvent
            providers.Factory(event_listeners.OptimizeSelectQueryListener),
            # ModuleObjectPatchedEvent
            providers.Factory(
                event_listeners.StoreImagesListener,
                service_factory=store_images_extractor_factory,
            ),
            providers.Factory(
                event_listeners.ExtractHtmlImagesListener,
                extractor_factory=html_images_extractor_factory,
            ),
        ),
    )
    event_manager = providers.Singleton(
        event_manager.EventManager,
        db=db,
        event_listeners=event_listeners,
    )

    publication = providers.Container(
        PublicationContainer,
        config=config,
        main_config=main_config,
        db=db,
        area_repository=area_repository,
        area_geometry_repository=area_geometry_repository,
        storage_file_repository=storage_file_repository,
        asset_repository=asset_repository,
    )
