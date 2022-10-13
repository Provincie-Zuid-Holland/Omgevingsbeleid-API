from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True, echo=settings.SQLALCHEMY_ECHO)
SessionLocal: Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
