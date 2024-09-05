from typing import Any, Dict, Optional

from pydantic import BaseSettings, validator


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
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_PORT: int = 1433
    TEST_DB_NAME: str = "test_db"

    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    SQLALCHEMY_TEST_DATABASE_URI: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str) and len(v):
            return v

        db_connection_settings = f"DRIVER={values['DB_DRIVER']};SERVER={values['DB_HOST']};DATABASE={values['DB_NAME']};UID={values['DB_USER']};PWD={values['DB_PASS']}"
        return "mssql+pyodbc:///?odbc_connect=%s" % db_connection_settings

    @validator("SQLALCHEMY_TEST_DATABASE_URI", pre=True)
    def assemble_test_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str) and len(v):
            return v

        db_connection_settings = f"DRIVER={values['DB_DRIVER']};SERVER={values['DB_HOST']};DATABASE={values['TEST_DB_NAME']};UID={values['DB_USER']};PWD={values['DB_PASS']}"
        return "mssql+pyodbc:///?odbc_connect=%s" % db_connection_settings

    # Dynamic
    MAIN_CONFIG_FILE: str = "./config/main.yml"
    OBJECT_CONFIG_PATH: str = "./config/objects/"

    # Mssql Search
    MSSQL_SEARCH_FTC_NAME: str = "Omgevingsbeleid_FTC"
    MSSQL_SEARCH_STOPLIST_NAME: str = "Omgevingsbeleid_SW"

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_nested_delimiter = "__"


core_settings = CoreSettings()
