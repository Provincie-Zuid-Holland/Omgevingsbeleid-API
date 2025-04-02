from typing import Any, Optional
from urllib.parse import quote_plus

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    PROJECT_VERSION: str = "3.0-alpha"
    DEBUG_MODE: bool = False
    LOCAL_DEVELOPMENT_MODE: bool = False

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
    DB_DRIVER: str = Field("ODBC Driver 17 for SQL Server", description="The driver for the SQL database")
    DB_HOST: str = Field("mssql", description="The host address of the database")
    DB_NAME: str = Field("development", description="The name of the database")
    DB_USER: str = Field("SA", description="The database username")
    DB_PASS: str = Field("Passw0rd", description="The password for the database user")
    TEST_DB_NAME: str = Field("db_test", description="The name of the test database")

    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    SQLALCHEMY_TEST_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str) and len(v):
            return v

        values = info.data
        db_connection_settings = (
            f"DRIVER={values['DB_DRIVER']};SERVER={values['DB_HOST']};"
            f"DATABASE={values['DB_NAME']};UID={values['DB_USER']};PWD={values['DB_PASS']}"
        )
        encoded_settings = quote_plus(db_connection_settings)

        return "mssql+pyodbc:///?odbc_connect=%s" % encoded_settings

    @field_validator("SQLALCHEMY_TEST_DATABASE_URI", mode="before")
    def assemble_test_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str) and len(v):
            return v

        values = info.data
        db_connection_settings = (
            f"DRIVER={values['DB_DRIVER']};SERVER={values['DB_HOST']};"
            f"DATABASE={values['TEST_DB_NAME']};UID={values['DB_USER']};PWD={values['DB_PASS']}"
        )
        encoded_settings = quote_plus(db_connection_settings)

        return "mssql+pyodbc:///?odbc_connect=%s" % encoded_settings

    # Dynamic
    MAIN_CONFIG_FILE: str = "./config/main.yml"
    OBJECT_CONFIG_PATH: str = "./config/objects/"

    # Mssql Search
    MSSQL_SEARCH_FTC_NAME: str = "Omgevingsbeleid_FTC"
    MSSQL_SEARCH_STOPLIST_NAME: str = "Omgevingsbeleid_SW"
    model_config = SettingsConfigDict(
        extra="allow",
        case_sensitive=True,
        env_file=".env",
        env_nested_delimiter="__",
    )


core_settings = CoreSettings()
