from datetime import datetime
from typing import Optional

from pydantic import create_model
from pydantic.config import BaseConfig
from pydantic.main import BaseModel
from sqlalchemy.inspection import inspect
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, String

from app.models.base import Status as StatusEnum


# Common inline schemas
class BeleidskeuzeShortInline(BaseModel):
    ID: int
    UUID: str
    Titel: str

    class Config:
        orm_mode = True


class GebruikerInline(BaseModel):
    Gebruikersnaam: str
    Rol: str
    Status: str
    UUID: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class LatestVersionInline(BaseModel):
    """
    Schema listing inline version of entity showing the latest
    version available.

    Used in /edits for Beleidskeuzes & Maatregelen
    """

    ID: int
    UUID: str

    Modified_Date: datetime
    Status: StatusEnum
    Titel: str

    Effective_Version: Optional[str]
    Type: str

    class Config:
        orm_mode = True


# Field aliassing
def strip_UUID(string: str) -> str:
    """
    Hack to strip _UUID off the json output since pydantic aliasses
    are broken with fastapi.
    """
    if string.endswith("_UUID"):
        return string[:-5]
    return string


def to_ref_field(string: str) -> str:
    """
    Custom alias for relationship objects in json output.
    Used to match the legacy api format: "Ref_*" fields
    """
    to_alias = [
        "Beleidskeuzes",
        "Beleidsmodules",
    ]

    if string not in to_alias:
        return string

    return "".join(["Ref_", string])


def valid_ref_alias(field: str) -> str:
    """
    Custom alias for relationship objects in json output.
    Used to match the legacy api format: "Ref_*" fields
    """
    aliasses = [
        "Beleidsdoelen",
        "Valid_Beleidsdoelen",
        "Beleidskeuzes",
        "Valid_Beleidskeuzes",
        "Beleidsmodules",
        "Valid_Beleidsmodules",
        "Maatregelen",
        "Valid_Maatregelen",
    ]

    if field in aliasses:
        if field.startswith("Valid_"):
            field = field[6:]

        field = "".join(["Ref_", field])
        return field

    return field


# Pydantic common methods


def create_pydantic_model(sqlalchemy_model):
    """
    Convert a sqlalchemy model to a simple pydantic schema
    base on defined column attributes.

    Used to DRY for Inline schemas in schemas.related
    """
    # Use the inspect module to extract column names and types
    inspector = inspect(sqlalchemy_model)
    fields = {}
    for cname, column in inspector.columns.items():
        # Map SQLAlchemy column types to Python data types
        python_type = (str, None)
        if isinstance(column.type, String):
            python_type = (str, None)
        elif isinstance(column.type, Integer):
            python_type = (int, None)
        elif isinstance(column.type, Boolean):
            python_type = (bool, None)
        elif isinstance(column.type, DateTime):
            python_type = (datetime, None)

        # Add the column name and type to the fields dictionary
        fields[str(cname)] = python_type

    # Pydantic config
    class InlineConfig(BaseConfig):
        orm_mode = True

    # Create the Pydantic model
    name = f"{sqlalchemy_model.__name__}Inline"
    pydantic_model = create_model(name, __config__=InlineConfig, **fields)
    return pydantic_model
