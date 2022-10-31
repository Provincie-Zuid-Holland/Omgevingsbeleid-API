from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings


router = APIRouter()


@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    gebruiker = crud.gebruiker.authenticate(
        db, username=form_data.username, password=form_data.password
    )

    if not gebruiker:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    elif not gebruiker.is_active():
        raise HTTPException(status_code=401, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    return {
        "access_token": security.create_access_token(
            gebruiker.UUID, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "identifier": gebruiker,
    }


@router.post("/login/test-token", response_model=schemas.Gebruiker)
def test_token(
    current_gebruiker: models.Gebruiker = Depends(deps.get_current_gebruiker),
) -> Any:
    """
    Test access token
    """
    return current_gebruiker
