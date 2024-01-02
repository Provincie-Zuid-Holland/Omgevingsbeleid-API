from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from app.core.dependencies import depends_db
from app.extensions.publications.repository import PublicationRepository


def depends_publication_repository(db: Session = Depends(depends_db)) -> PublicationRepository:
    return PublicationRepository(db)
