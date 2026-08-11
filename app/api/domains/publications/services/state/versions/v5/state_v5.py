
from pydantic import Field

from app.api.domains.publications.services.state.state import State
from app.api.domains.publications.services.state.versions.v5 import models


class StateV5(State):
    Purposes: dict[str, models.Purpose] = Field({})
    Acts: dict[str, models.ActiveAct] = Field({})
    Announcements: dict[str, models.ActiveAnnouncement] = Field({})

    @staticmethod
    def get_schema_version() -> int:
        return 5

    def get_data(self) -> dict:
        data: dict = self.model_dump()
        return data
