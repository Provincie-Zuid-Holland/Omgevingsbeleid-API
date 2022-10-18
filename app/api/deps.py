from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.crud.crud_gebruiker import gebruiker as crud_gebruiker
from app.db.session import SessionLocal
from app.models.gebruiker import Gebruiker
from app.schemas import TokenPayload
from app.schemas.filters import FilterCombiner, Filters

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V01_STR}/login/access-token"
)


def string_filters(
    all_filters: Optional[str] = None,
    any_filters: Optional[str] = None,
) -> Filters:
    filters = Filters()
    if all_filters:
        filters.add_from_string(FilterCombiner.AND, all_filters)

    if any_filters:
        filters.add_from_string(FilterCombiner.OR, any_filters)

    return filters


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_gebruiker(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> Gebruiker:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kan inloggegevens niet valideren",
        )

    gebruiker = crud_gebruiker.get(uuid=token_data.sub)

    if not gebruiker:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    return gebruiker


def get_current_active_gebruiker(
    current_gebruiker: Gebruiker = Depends(get_current_gebruiker),
) -> Gebruiker:
    if not crud_gebruiker.is_active(current_gebruiker):
        raise HTTPException(status_code=400, detail="Gebruiker is inactief")
    return current_gebruiker


def get_current_active_super_gebruiker(
    current_gebruiker: Gebruiker = Depends(get_current_gebruiker),
) -> Gebruiker:
    if not crud_gebruiker.is_supergebruiker(current_gebruiker):
        raise HTTPException(
            status_code=400, detail="De gebruiker heeft niet genoeg rechten"
        )
    return current_gebruiker
