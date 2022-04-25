from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_gebruiker(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.Gebruiker:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kan inloggegevens niet valideren",
        )
    gebruiker = crud.gebruiker.get(db, id=token_data.sub)
    if not gebruiker:
        raise HTTPException(status_code=404, detail="Gebruiker niuet gevonden")
    return gebruiker


def get_current_active_gebruiker(
    current_gebruiker: models.Gebruiker = Depends(get_current_gebruiker),
) -> models.Gebruiker:
    if not crud.gebruiker.is_active(current_gebruiker):
        raise HTTPException(status_code=400, detail="Gebruiker is inactief")
    return current_gebruiker


def get_current_active_supergebruiker(
    current_gebruiker: models.Gebruiker = Depends(get_current_gebruiker),
) -> models.Gebruiker:
    if not crud.gebruiker.is_supergebruiker(current_gebruiker):
        raise HTTPException(
            status_code=400, detail="De gebruiker heeft niet genoeg rechten"
        )
    return current_gebruiker
