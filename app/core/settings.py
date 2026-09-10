from typing import Any, Self

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

    SECRET_KEY: str = "secret-key-which-is-at-least-32-bytes-long"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4

    # Database
    SQLALCHEMY_ECHO: bool = True
    DB_DRIVER: str = Field("PostgreSQL Unicode", description="The driver for the SQL database")
    DB_HOST: str = Field("postgres", description="The host address of the database")
    DB_NAME: str = Field("omgevingsbeleid", description="The name of the database")
    DB_USER: str = Field("pzh", description="The database username")
    DB_PASS: str = Field("password", description="The password for the database user")
    DB_PORT: str = Field("5432", description="The port for the database connection")
    DB_DIALECT: str = Field("postgresql+psycopg", description="The dialect for the database")
    TEST_DB_NAME: str = Field("db_test", description="The name of the test database")

    SQLALCHEMY_DATABASE_URI: str = ""
    SQLALCHEMY_TEST_DATABASE_URI: str = ""

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: str | None, info) -> Any:
        if isinstance(v, str) and len(v):
            return v

        values = info.data
        return f"{values['DB_DIALECT']}://{values['DB_USER']}:{values['DB_PASS']}@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}"

    @field_validator("SQLALCHEMY_TEST_DATABASE_URI", mode="before")
    def assemble_test_db_connection(cls, v: str | None, info) -> Any:
        if isinstance(v, str) and len(v):
            return v

        values = info.data
        return f"{values['DB_DIALECT']}://{values['DB_USER']}:{values['DB_PASS']}@{values['DB_HOST']}:{values['DB_PORT']}/{values['TEST_DB_NAME']}"

    # Dynamic
    MAIN_CONFIG_FILE: str = "./config/main.yml"
    OBJECT_CONFIG_PATH: str = "./config/objects/"

    # Mssql Search
    MSSQL_SEARCH_FTC_NAME: str = "Omgevingsbeleid_FTC"
    MSSQL_SEARCH_STOPLIST_NAME: str = "Omgevingsbeleid_SW"

    PUBLICATION_KOOP: dict[str, KoopSettings] = Field(default_factory=dict)
    PUBLICATION_OW_DATASET: str = Field(
        "provincie Zuid-holland",
        description="Dataset identifier for OW (Omgevingswet) publications",
    )
    PUBLICATION_OW_GEBIED: str = Field(
        "provincie Zuid-holland",
        description="Area identifier for OW (Omgevingswet) publications",
    )

    # @note: These will be overwritten and based on earlier input
    # These are for the Dependency Injector library

    DB_TYPE: str = Field("")
    DEBUG_MODE_STR: str = Field("")

    @model_validator(mode="after")
    def set_values_for_containers(self) -> Self:
        self.DEBUG_MODE_STR = "yes" if self.DEBUG_MODE else "no"
        # "mssql+pyodbc://..." → "mssql"
        # "sqlite+pysqlite:///..." → "sqlite"
        # "sqlite:///:memory:" → "sqlite"
        self.DB_TYPE = self.SQLALCHEMY_DATABASE_URI.split("://", 1)[0].split("+")[0]
        return self

    model_config = SettingsConfigDict(
        extra="allow",
        case_sensitive=True,
        env_file=".env",
        env_nested_delimiter="__",
    )
