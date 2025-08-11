from typing import Any, Dict, Optional, Self
from urllib.parse import quote_plus

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class KoopSettings(BaseModel):
    API_KEY: str
    RENVOOI_API_URL: str
    PREVIEW_API_URL: str


class Settings(BaseSettings):
    PROJECT_VERSION: str = "5.0.0"
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

    SQLALCHEMY_DATABASE_URI: str = ""
    SQLALCHEMY_TEST_DATABASE_URI: str = ""

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str) and len(v):
            return v

        values = info.data
        db_connection_settings = f"DRIVER={values['DB_DRIVER']};SERVER={values['DB_HOST']};DATABASE={values['DB_NAME']};UID={values['DB_USER']};PWD={values['DB_PASS']}"
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

    PUBLICATION_KOOP: Dict[str, KoopSettings] = Field(default_factory=dict)
    PUBLICATION_OW_DATASET: str = Field(
        "provincie Zuid-holland",
        description="Dataset identifier for OW (Omgevingswet) publications",
    )
    PUBLICATION_OW_GEBIED: str = Field(
        "provincie Zuid-holland",
        description="Area identifier for OW (Omgevingswet) publications",
    )

    # @note: These will be overwritten and based on earlier input
    # These are for the Depedency Injector library

    DB_TYPE: str = Field("")
    DEBUG_MODE_STR: str = Field("")

    @model_validator(mode="after")
    def set_values_for_containers(self) -> Self:
        self.DEBUG_MODE_STR = "yes" if self.DEBUG_MODE else "no"
        self.DB_TYPE = self.SQLALCHEMY_DATABASE_URI.split("+")[0]
        return self

    model_config = SettingsConfigDict(
        extra="allow",
        case_sensitive=True,
        env_file=".env",
        env_nested_delimiter="__",
    )
