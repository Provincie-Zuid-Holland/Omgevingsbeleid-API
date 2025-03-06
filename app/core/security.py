import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.settings.dynamic_settings import DynamicSettings

ALGORITHM = "HS256"


class Security:
    def __init__(self, settings: DynamicSettings):
        self._settings: DynamicSettings = settings
        self._pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(
        self,
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        if self._settings.DEBUG_MODE:
            expires_delta = timedelta(days=5)  # longer for dev

        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, self._settings.SECRET_KEY, algorithm=ALGORITHM)

        return encoded_jwt

    def verify_password(
        self,
        plain_password: Optional[str],
        hashed_password: Optional[str],
    ) -> bool:
        if plain_password is None:
            return False
        if hashed_password is None:
            return False
        return self._pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def get_random_password(self, length: int = 32):
        alphabet = string.ascii_letters + string.digits
        password = "".join(secrets.choice(alphabet) for i in range(length))
        return password
