from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Select


@dataclass
class PreparedQuery:
    query: Select
    aliased_ref: Any  # @see sqlalchemy.orm.aliased


class ResponseOK(BaseModel):
    message: str
