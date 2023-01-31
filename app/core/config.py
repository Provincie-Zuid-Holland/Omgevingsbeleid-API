from datetime import datetime
from functools import lru_cache
import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, validator


class Settings(BaseSettings):
    API_V01_STR: str = "/v0.1"

    DEBUG_MODE: bool = bool(os.getenv("DEBUG_MODE", 0))

    SECRET_KEY: str = os.getenv("JWT_SECRET", "secret")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4

    # SERVER_NAME: str
    # SERVER_HOST: AnyHttpUrl

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str = "Omgevingsbeleid API"
    PROJECT_DESC: str = """
        This API serves all the object that make up the policies 
        of a provincial government. 
        """
    PROJECT_VERSION: str = "1.1.10"
    OPENAPI_LOGO: str = "https://avatars.githubusercontent.com/u/60095455?s=200&v=4"

    # SENTRY_DSN: Optional[HttpUrl] = None
    # @validator("SENTRY_DSN", pre=True)
    # def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
    #     if len(v) == 0:
    #         return None
    #     return v

    DB_DRIVER: str = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    DB_HOST: str = os.getenv("DB_HOST", "mssql")
    DB_NAME: str = os.getenv("DB_NAME", "development")
    DB_USER: str = os.getenv("DB_USER", "SA")
    DB_PASS: str = os.getenv("DB_PASS", "Passw0rd")
    TEST_DB_NAME: str = os.getenv("TEST_DB_NAME", "db_test")

    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v

        db_connection_settings = f"DRIVER={values['DB_DRIVER']};SERVER={values['DB_HOST']};DATABASE={values['DB_NAME']};UID={values['DB_USER']};PWD={values['DB_PASS']}"

        return "mssql+pyodbc:///?odbc_connect=%s" % db_connection_settings

    SQLALCHEMY_TEST_DATABASE_URI: Optional[str] = None

    @validator("SQLALCHEMY_TEST_DATABASE_URI", pre=True)
    def assemble_test_db_connection(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, str):
            return v

        db_connection_settings = f"DRIVER={values['DB_DRIVER']};SERVER={values['DB_HOST']};DATABASE={values['TEST_DB_NAME']};UID={values['DB_USER']};PWD={values['DB_PASS']}"
        return "mssql+pyodbc:///?odbc_connect=%s" % db_connection_settings

    SQLALCHEMY_ECHO: bool = False

    # Constants
    MIN_DATETIME: datetime = datetime(1753, 1, 1, 0, 0, 0)
    MAX_DATETIME: datetime = datetime(9999, 12, 31, 23, 59, 59)
    NULL_UUID: str = "00000000-0000-0000-0000-000000000000"

    class Config:
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
