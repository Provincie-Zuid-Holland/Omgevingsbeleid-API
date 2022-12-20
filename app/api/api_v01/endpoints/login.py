from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app import schemas
from app.api import deps
from app.crud import CRUDGebruiker
from app.core import security
from app.core.config import settings


router = APIRouter()


@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    crud_gebruiker: CRUDGebruiker = Depends(deps.get_crud_gebruiker),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    gebruiker = crud_gebruiker.authenticate(
        username=form_data.username,
        password=form_data.password,
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
