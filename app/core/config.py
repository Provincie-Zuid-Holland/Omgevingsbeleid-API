import secrets
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl, PostgresDsn, validator


class Settings(BaseSettings):
    API_V01_STR: str = "/v0.1"

    SECRET_KEY: str = "abc" # @todo: secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4
    # SERVER_NAME: str
    # SERVER_HOST: AnyHttpUrl

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str = "Omgevingsbeleid API"
    # SENTRY_DSN: Optional[HttpUrl] = None

    # @validator("SENTRY_DSN", pre=True)
    # def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
    #     if len(v) == 0:
    #         return None
    #     return v

    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    DB_HOST: str = "mssql"
    DB_NAME: str = "SA"
    DB_USER: str = "db_dev"
    DB_PASS: str = "Passw0rd"

    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v

        db_connection_settings = f"DRIVER={os.getenv('DB_DRIVER')};SERVER={os.getenv('DB_HOST')};DATABASE={os.getenv('DB_NAME')};UID={os.getenv('DB_USER')};PWD={os.getenv('DB_PASS')}"
        return "mssql+pyodbc:///?odbc_connect=%s" % db_connection_settings

    SQLALCHEMY_ECHO: bool = False

    # Constants
    MIN_DATETIME: datetime = datetime(1753, 1, 1, 0, 0, 0)
    MAX_DATETIME: datetime = datetime(9999, 12, 31, 23, 59, 59)
    NULL_UUID: str = "00000000-0000-0000-0000-000000000000"

    class Config:
        case_sensitive = True


settings = Settings()

