from typing import Any, Self

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class KoopSettings(BaseModel):
    API_KEY: str
    RENVOOI_API_URL: str
    PREVIEW_API_URL: str


class Settings(BaseSettings):
    PROJECT_VERSION: str = "5.0.0"

    PROJECT_NAME: str = "Omgevingsbeleid API"
    PROJECT_DESC: str = """
        This API serves all the object that make up the policies 
        of a provincial government. 
        """
    OPENAPI_LOGO: str = "https://avatars.githubusercontent.com/u/60095455?s=200&v=4"

    SECRET_KEY: str = "secret-key-which-is-at-least-32-bytes-long"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4

    # Database
    SQLALCHEMY_ECHO: bool = False

    DB_DIALECT: str = Field(
        "postgresql+psycopg",
        description="SQLAlchemy dialect+driver, e.g. postgresql+psycopg or sqlite+pysqlite",
    )
    DB_HOST: str = Field("postgres", description="The host address of the database")
    DB_PORT: int = Field(5432, description="The port for the database connection")
    DB_NAME: str = Field("omgevingsbeleid", description="The name of the database")
    DB_USER: str = Field("omgevingsbeleid", description="The database username")
    DB_PASS: str = Field("omgevingsbeleid", description="The password for the database user")

    SQLALCHEMY_DATABASE_URI: str = ""

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: str | None, info) -> Any:
        if isinstance(v, str) and len(v):
            return v

        values = info.data
        return URL.create(
            values["DB_DIALECT"],
            username=values["DB_USER"],
            password=values["DB_PASS"],
            host=values["DB_HOST"],
            port=values["DB_PORT"],
            database=values["DB_NAME"],
        ).render_as_string(hide_password=False)

    # Dynamic
    MAIN_CONFIG_FILE: str = "./config/main.yml"
    OBJECT_CONFIG_PATH: str = "./config/objects/"

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

    @model_validator(mode="after")
    def set_values_for_containers(self) -> Self:
        # "sqlite+pysqlite:///..." → "sqlite"
        # "sqlite:///:memory:" → "sqlite"
        db_type: str = self.SQLALCHEMY_DATABASE_URI.split("://", 1)[0].split("+")[0]
        db_type_map: dict[str, str] = {"postgresql": "postgres"}
        if db_type in db_type_map:
            db_type = db_type_map[db_type]

        valid_db_types: set[str] = {"sqlite", "postgres"}
        if db_type not in valid_db_types:
            raise RuntimeError(
                f"DB_TYPE `{db_type}` is not supported. Supported databases are {', '.join(valid_db_types)}"
            )
        self.DB_TYPE = db_type

        return self

    model_config = SettingsConfigDict(
        extra="allow",
        case_sensitive=True,
        env_file=".env",
        env_nested_delimiter="__",
    )
