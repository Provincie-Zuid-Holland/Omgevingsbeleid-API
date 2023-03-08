from datetime import datetime
import os
from typing import Any, Dict, Optional

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    PROJECT_VERSION: str = "3.0-alpha"
    DEBUG_MODE: bool = True

    PROJECT_NAME: str = "Omgevingsbeleid API"
    PROJECT_DESC: str = """
        This API serves all the object that make up the policies 
        of a provincial government. 
        """
    OPENAPI_LOGO: str = "https://avatars.githubusercontent.com/u/60095455?s=200&v=4"

    SECRET_KEY: str = "secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4

    # Database
    SQLALCHEMY_ECHO: bool = True
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

    # Dynamic
    MAIN_CONFIG_FILE: str = "./config/main.yml"
    OBJECT_CONFIG_PATH: str = "./config/objects/"

    # Constants
    MAX_DATETIME: datetime = datetime(9999, 12, 31, 23, 59, 59)

    class Config:
        case_sensitive = True
        env_file = ".env"


def settings_factory():
    return Settings()


settings = settings_factory()
