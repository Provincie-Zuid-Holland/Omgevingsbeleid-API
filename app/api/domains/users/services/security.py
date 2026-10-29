import re
import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Any

import anyio
import jwt
from fastapi import HTTPException, status
from jwt import PyJWTError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher
from pydantic import ValidationError

from app.api.domains.users.types import TokenPayload


class Security:
    ALGORITHM = "HS256"

    _BCRYPT_MAX_BYTES = 72

    # Password hashing is CPU-heavy. So cap how many hashes run at once
    _MAX_CONCURRENT_HASHES = 8

    def __init__(
        self,
        secret_key: str,
        token_lifetime: timedelta,
    ):
        self._secret_key: str = secret_key
        self._token_lifetime: timedelta = token_lifetime
        self._pwd_hash: PasswordHash = PasswordHash(
            (
                Argon2Hasher(),
                BcryptHasher(),
            )
        )
        self._hash_limiter = anyio.CapacityLimiter(self._MAX_CONCURRENT_HASHES)

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
        subject: str | Any,
    ) -> str:
        expire = datetime.now(UTC) + self._token_lifetime
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self.ALGORITHM)

        return encoded_jwt

    async def verify_password(
        self,
        plain_password: str | None,
        hashed_password: str | None,
    ) -> bool:
        return await anyio.to_thread.run_sync(
            self.verify_password_sync,
            plain_password,
            hashed_password,
            limiter=self._hash_limiter,
        )

    async def get_password_hash(self, password: str) -> str:
        return await anyio.to_thread.run_sync(
            self.get_password_hash_sync,
            password,
            limiter=self._hash_limiter,
        )

    def verify_password_sync(
        self,
        plain_password: str | None,
        hashed_password: str | None,
    ) -> bool:
        if plain_password is None:
            return False
        if hashed_password is None:
            return False

        variants = {
            plain_password,
            plain_password.strip(),
        }
        try:
            return any(
                self._pwd_hash.verify(self._prepare_for_hash(p, hashed_password), hashed_password) for p in variants
            )
        except (UnknownHashError, ValueError):
            return False

    def get_password_hash_sync(self, password: str) -> str:
        return self._pwd_hash.hash(password)

    def validate_password(self, password: str) -> str:
        """Trim and validate password against complexity requirements.

        Returns the trimmed password if valid, raises HTTPException otherwise.
        """
        password = password.strip()

        if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{12,}$", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 12 characters long and include at least one uppercase letter, one lowercase letter, one number, and one special character.",
            )

        return password

    def get_random_password(self, length: int = 32) -> str:
        alphabet = string.ascii_letters + string.digits
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        return password

    def _prepare_for_hash(self, password: str, hashed_password: str) -> str | bytes:
        # Truncate the password to 72 bytes when checking it against a bcrypt hash for legacy reasons
        if not hashed_password.startswith("$2"):
            return password

        encoded = password.encode("utf-8")
        if len(encoded) <= self._BCRYPT_MAX_BYTES:
            return password
        return encoded[: self._BCRYPT_MAX_BYTES]
