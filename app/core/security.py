from datetime import datetime, timedelta
import logging
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"
logger = logging.getLogger(__name__)

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(60*4)

    if settings.DEBUG_MODE:
        expires_delta = timedelta(60*99) #longer for dev

    expire = datetime.utcnow() + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    if settings.DEBUG_MODE:  
        logger.debug("\n\n")
        logger.debug(to_encode)
        logger.debug("\n\n")
        logger.debug(encoded_jwt)
        logger.debug("\n\n")

    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
