import sqlite3

from sqlalchemy import NullPool, create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session

from app.core.settings import settings


def _enable_sqlite_load_extension(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.enable_load_extension(True)
        dbapi_connection.execute('SELECT load_extension("mod_spatialite")')
        dbapi_connection.load_extension("mod_spatialite")


engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=settings.SQLALCHEMY_ECHO,
    # pool_size=100,
    # max_overflow=200,
    # poolclass=NullPool,
)
if engine.dialect.name == "sqlite":
    event.listen(engine, "connect", _enable_sqlite_load_extension)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# ScopedSessionLocal = scoped_session(SessionLocal)


engine_with_auto_commit = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=settings.SQLALCHEMY_ECHO,
    isolation_level="AUTOCOMMIT",
)
if engine_with_auto_commit.dialect.name == "sqlite":
    event.listen(engine_with_auto_commit, "connect", _enable_sqlite_load_extension)
SessionLocalWithAutoCommit = sessionmaker(autoflush=False, bind=engine_with_auto_commit)
