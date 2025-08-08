from typing import Dict

from pydantic import Field

from app.api.domains.publications.services.state.state import State
from app.api.domains.publications.services.state.versions.v4 import models


class StateV4(State):
    Purposes: Dict[str, models.Purpose] = Field({})
    Acts: Dict[str, models.ActiveAct] = Field({})
    Announcements: Dict[str, models.ActiveAnnouncement] = Field({})

    @staticmethod
    def get_schema_version() -> int:
        return 4

    def get_data(self) -> dict:
        data: dict = self.model_dump()
        return data
