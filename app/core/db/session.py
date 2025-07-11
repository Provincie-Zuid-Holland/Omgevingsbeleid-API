import sqlite3
from contextlib import AbstractContextManager, contextmanager
from typing import Callable

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session

SessionFactoryType = Callable[..., AbstractContextManager[Session]]


def _enable_sqlite_load_extension(dbapi_connection, connection_record) -> None:  # noqa
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.enable_load_extension(True)
        dbapi_connection.execute('SELECT load_extension("mod_spatialite")')
        dbapi_connection.load_extension("mod_spatialite")


def create_db_engine(uri: str, echo: str) -> Engine:
    engine = create_engine(
        uri,
        pool_pre_ping=True,
        echo=echo,
    )
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _enable_sqlite_load_extension)

    return engine


@contextmanager
def session_scope(session_factory: SessionFactoryType):
    with session_factory() as session:
        try:
            # when using SQLite, ensure FK constraints and load Spatialite
            if session.bind.dialect.name == "sqlite":
                session.execute(text("PRAGMA foreign_keys = ON"))
                session.execute(text("SELECT load_extension('mod_spatialite')"))
            yield session
            # commit happens automatically when exiting the 'with' block
        except Exception:
            session.rollback()
            raise
