import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import jwt
from fastapi import HTTPException, status
from jwt import PyJWTError
from passlib.context import CryptContext
from pydantic import ValidationError

from app.api.domains.users.types import TokenPayload


class Security:
    ALGORITHM = "HS256"

    def __init__(
        self,
        secret_key: str,
        token_lifetime: timedelta,
    ):
        self._secret_key: str = secret_key
        self._token_lifetime: timedelta = token_lifetime
        self._pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def decode_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self.ALGORITHM])
            token_data = TokenPayload(**payload)
        except (PyJWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate authorization token",
            )
        return token_data

    def create_access_token(
        self,
        subject: Union[str, Any],
    ) -> str:
        expire = datetime.now(timezone.utc) + self._token_lifetime
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self.ALGORITHM)

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
