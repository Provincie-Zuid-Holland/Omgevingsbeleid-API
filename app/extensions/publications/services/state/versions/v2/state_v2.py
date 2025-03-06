from typing import Dict

from pydantic import Field

from app.extensions.publications.services.state.state import State
from app.extensions.publications.services.state.versions.v2 import models


class StateV2(State):
    Purposes: Dict[str, models.Purpose] = Field({})
    Acts: Dict[str, models.ActiveAct] = Field({})
    Announcements: Dict[str, models.ActiveAnnouncement] = Field({})

    @staticmethod
    def get_schema_version() -> int:
        return 2

    def get_data(self) -> dict:
        data: dict = self.model_dump()
        return data
