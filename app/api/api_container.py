from datetime import timedelta

from dependency_injector import containers, providers
from sqlalchemy.orm import sessionmaker

import app.api.domains.objects.services as object_services
import app.api.domains.users.services as user_services
import app.api.domains.werkingsgebieden.repositories as werkingsgebieden_repositories
import app.api.domains.werkingsgebieden.services as werkingsgebied_services
import app.api.events.retrieved_objects_event_listeners as retrieved_objects_event_listeners
from app.api.domains.objects import object_repository
from app.core.db.session import create_db_engine, init_db_session
from app.core.services.event import event_manager
from app.core.settings import Settings


class ApiContainer(containers.DeclarativeContainer):
    models_provider = providers.Dependency()

    config = providers.Configuration(pydantic_settings=[Settings()])

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

    object_repository = providers.Factory(object_repository.ObjectRepository, db=db)
    werkingsgebieden_repository = providers.Factory(werkingsgebieden_repositories.WerkingsgebiedenRepository, db=db)
    sqlite_geometry_repository = providers.Factory(werkingsgebieden_repositories.SqliteGeometryRepository, db=db)
    sqlite_area_geometry_repository = providers.Factory(
        werkingsgebieden_repositories.SqliteAreaGeometryRepository,
        db=db,
    )
    mssql_geometry_repository = providers.Factory(werkingsgebieden_repositories.MssqlGeometryRepository, db=db)
    mssql_area_geometry_repository = providers.Factory(werkingsgebieden_repositories.MssqlAreaGeometryRepository, db=db)

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

    access_token_lifetime = providers.Selector(
        config.DEBUG_MODE_STR,
        yes=providers.Object(timedelta(days=5)),
        no=providers.Callable(timedelta, minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    security = providers.Factory(
        user_services.Security,
        secret_key=config.SECRET_KEY,
        token_lifetime=access_token_lifetime,
    )

    add_relations_service_factory = providers.Singleton(
        object_services.AddRelationsServiceFactory,
        db=db,
    )
    join_werkingsgebieden_service_factory = providers.Singleton(
        werkingsgebied_services.JoinWerkingsgebiedenServiceFactory,
        db=db,
    )

    event_listeners = providers.Factory(
        event_manager.EventListeners,
        listeners=providers.List(
            providers.Factory(
                retrieved_objects_event_listeners.AddRelationsToObjectsListener,
                relations_factory=add_relations_service_factory,
            ),
            providers.Factory(
                retrieved_objects_event_listeners.JoinWerkingsgebeidenToObjectsListener,
                service_factory=join_werkingsgebieden_service_factory,
            ),
        ),
    )
    event_manager = providers.Singleton(
        event_manager.EventManager,
        db=db,
        event_listeners=event_listeners,
    )
