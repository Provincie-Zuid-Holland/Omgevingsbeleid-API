from dependency_injector import containers, providers
from sqlalchemy.orm import sessionmaker

from app.api.domains.objects import object_repository
from app.core.db.session import create_db_engine, init_db_session
from app.core.settings import Settings


class ApiContainer(containers.DeclarativeContainer):
    settings = providers.Singleton(Settings)

    db_engine = providers.Singleton(create_db_engine, settings=settings)
    db_session_factory = providers.Singleton(sessionmaker, bind=db_engine, autocommit=False, autoflush=False)
    db = providers.Resource(
        init_db_session,
        session_factory=db_session_factory,
    )

    object_repository = providers.Factory(
        object_repository.ObjectRepository,
        db=db,
    )
