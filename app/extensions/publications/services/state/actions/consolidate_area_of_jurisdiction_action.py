import uuid

from app.extensions.publications.models.api_input_data import ActFrbr
from app.extensions.publications.services.state.actions.action import Action


class ConsolidateAreaOfJurisdictionAction(Action):
    UUID: uuid.UUID
    Administrative_Borders_ID: str
    Act_Frbr: ActFrbr

    def __repr__(self) -> str:
        return f"""
        ConsolidateAreaOfJurisdictionAction(
            UUID="{self.UUID}",
            Administrative_Borders_ID="{self.Administrative_Borders_ID}",
            Act_Frbr={self.Act_Frbr},
        )
        """
