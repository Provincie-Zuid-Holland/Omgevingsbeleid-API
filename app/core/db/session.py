import sqlite3
from typing import Generator

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.core.settings import Settings


def _enable_sqlite_load_extension(dbapi_connection, connection_record) -> None:  # noqa
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.enable_load_extension(True)
        dbapi_connection.execute('SELECT load_extension("mod_spatialite")')
        dbapi_connection.load_extension("mod_spatialite")


def create_db_engine(settings: Settings) -> Engine:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        pool_pre_ping=True,
        echo=settings.SQLALCHEMY_ECHO,
    )
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _enable_sqlite_load_extension)

    return engine


def create_db_engine_with_autocommit(settings: Settings) -> Engine:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        pool_pre_ping=True,
        echo=settings.SQLALCHEMY_ECHO,
        isolation_level="AUTOCOMMIT",
    )
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _enable_sqlite_load_extension)

    return engine


def init_db_session(session_factory: sessionmaker) -> Generator[sessionmaker, None]:
    with session_factory() as db:
        try:
            if db.bind.dialect.name == "sqlite":
                db.execute(text("pragma foreign_keys=on"))
                db.execute(text("SELECT load_extension('mod_spatialite')"))
            yield db
        except Exception as e:
            # Gives me a place to inspect
            raise e
