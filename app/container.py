from dependency_injector import containers, providers
from sqlalchemy.orm import sessionmaker

from app.build.build_container import BuildContainer
from app.core.db.session import create_db_engine, create_db_engine_with_autocommit, init_db_session
from app.core.models_provider import ModelsProvider
from app.core.settings import Settings


class Container(containers.DeclarativeContainer):
    """
    This is the main container for the application.
    """

    settings = providers.Singleton(Settings)

    db_engine = providers.Singleton(create_db_engine, settings=settings)
    db_session_factory = providers.Singleton(sessionmaker, bind=db_engine, autocommit=False, autoflush=False)
    db = providers.Resource(
        init_db_session,
        session_factory=db_session_factory,
    )

    # @todo: Should check if we can remove this
    db_engine_auto = providers.Singleton(create_db_engine_with_autocommit, settings=settings)
    db_session_auto_factory = providers.Singleton(sessionmaker, bind=db_engine, autocommit=True, autoflush=False)

    models_provider = providers.Singleton(ModelsProvider)

    build_package = providers.Container(
        BuildContainer,
        settings=settings,
        db=db,
        models_provider=models_provider,
    )
