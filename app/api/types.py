from dataclasses import dataclass
from typing import Any, Union

from pydantic import BaseModel, Field
from sqlalchemy import CompoundSelect, Select


@dataclass
class PreparedQuery:
    query: Select
    aliased_ref: Any  # @see sqlalchemy.orm.aliased


class ResponseOK(BaseModel):
    message: str = Field("OK")


# Both can be used by stmt.execute() but Executable type was not appropriate
Selectable = Union[Select, CompoundSelect]
