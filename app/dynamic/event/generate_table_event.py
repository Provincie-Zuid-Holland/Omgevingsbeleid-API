from typing import Type

from .types import Event
from ..config.models import Column
from app.core.db import Base


class GenerateTableEvent(Event):
    def __init__(
        self,
        table_type: Type[Base],
        table_name: str,
        column: Column,
    ):
        super().__init__()
        self.table_type: Type[Base] = table_type
        self.table_name: str = table_name
        self.column: Column = column
