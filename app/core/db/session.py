from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=settings.SQLALCHEMY_ECHO,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

engine_with_auto_commit = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=settings.SQLALCHEMY_ECHO,
    isolation_level="AUTOCOMMIT",
)
SessionLocalWithAutoCommit = sessionmaker(autoflush=False, bind=engine_with_auto_commit)
