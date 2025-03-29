from dependency_injector import containers, providers

from sqlalchemy.orm import sessionmaker

from app.core.db.session import create_db_engine, create_db_engine_with_autocommit, init_db_session
from app.core.settings import Settings


class BuilderContainer(containers.DeclarativeContainer):
    settings = providers.Singleton(Settings)

    main_config = providers.Configuration(yaml_files=["./config/main.yml"])
    
    db_engine = providers.Singleton(create_db_engine, settings=settings)
    db_session_factory = providers.Singleton(sessionmaker, bind=db_engine, autocommit=False, autoflush=False)
    db = providers.Resource(
        init_db_session,
        session_factory=db_session_factory,
    )

    # @todo: Should check if we can remove this
    db_engine_auto = providers.Singleton(create_db_engine_with_autocommit, settings=settings)
    db_session_auto_factory = providers.Singleton(sessionmaker, bind=db_engine, autocommit=True, autoflush=False)

