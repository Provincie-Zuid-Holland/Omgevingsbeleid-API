from typing import Callable, Optional
from uuid import UUID

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.dependencies import depends_db

from app.core.settings import settings
from app.core.security import ALGORITHM
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.model import TokenPayload
from app.extensions.users.repository.user_repository import UserRepository


reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"/login/access-token")


def require_auth(_: str = Depends(reusable_oauth2)):
    pass


def depends_user_repository(db: Session = Depends(depends_db)) -> UserRepository:
    return UserRepository(db)


def depends_current_user(
    token: str = Depends(reusable_oauth2),
    user_repository: UserRepository = Depends(depends_user_repository),
) -> GebruikersTable:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kan inloggegevens niet valideren",
        )

    user_uuid: str = token_data.sub
    as_uuid: UUID = UUID(user_uuid)
    maybe_user: Optional[GebruikersTable] = user_repository.get_by_uuid(as_uuid)
    if not maybe_user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    return maybe_user


def depends_current_active_user(
    current_user: GebruikersTable = Depends(depends_current_user),
) -> GebruikersTable:
    if not current_user.IsActief:
        raise HTTPException(status_code=400, detail="Gebruiker is inactief")
    return current_user


def depends_current_active_user_with_role_curried(
    required_role: Optional[str],
) -> Callable:
    def depends_current_active_user_with_role(
        current_user: GebruikersTable = Depends(depends_current_active_user),
    ):
        if not required_role:
            return current_user
        if required_role != current_user.Rol:
            raise HTTPException(status_code=401, detail="Invalid user role")
        return current_user

    return depends_current_active_user_with_role
