from typing import Type

from app.build.events.types import BuildEvent
from app.core.db.base import Base
from app.core.types import Column


class GenerateTableEvent(BuildEvent):
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
