from typing import Generator, Optional
from app.schemas.filters import FilterCombiner, Filters

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
) -> models.Gebruiker:

    from pprint import pprint

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as err:
        pprint(err)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kan inloggegevens niet valideren",
        )
    print("\n\n")
    print(token_data)
    print("\n\n")

    gebruiker = crud.gebruiker.get(uuid=token_data.sub)

    pprint(gebruiker)
    pprint(gebruiker.Email)

    if not gebruiker:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    print("return the gebruiker")
    return gebruiker


def get_current_active_gebruiker(
    current_gebruiker: models.Gebruiker = Depends(get_current_gebruiker),
) -> models.Gebruiker:
    if not crud.gebruiker.is_active(current_gebruiker):
        raise HTTPException(status_code=400, detail="Gebruiker is inactief")
    return current_gebruiker


def get_current_active_super_gebruiker(
    current_gebruiker: models.Gebruiker = Depends(get_current_gebruiker),
) -> models.Gebruiker:
    if not crud.gebruiker.is_supergebruiker(current_gebruiker):
        raise HTTPException(
            status_code=400, detail="De gebruiker heeft niet genoeg rechten"
        )
    return current_gebruiker
