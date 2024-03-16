import uuid

from app.extensions.publications.models.api_input_data import ActFrbr
from app.extensions.publications.services.state.actions.action import Action


class ConsolidateWerkingsgebiedAction(Action):
    UUID: uuid.UUID
    Object_ID: int
    Work: str
    Expression_Version: str
    Act_Frbr: ActFrbr

    def __repr__(self) -> str:
        return f"""
        ConsolidateWerkingsgebiedAction(
            UUID="{self.UUID}",
            Object_ID="{self.Object_ID}",
            Work="{self.Work}",
            Expression_Version="{self.Expression_Version}",
            Act_Frbr={self.Act_Frbr},
        )
        """
