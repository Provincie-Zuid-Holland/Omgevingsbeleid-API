import uuid

from app.extensions.publications.models.api_input_data import ActFrbr, Purpose
from app.extensions.publications.services.state.actions.action import Action


class ConsolidateWerkingsgebiedAction(Action):
    UUID: uuid.UUID
    Object_ID: int
    Work: str
    Expression_Version: str
    Act_Frbr: ActFrbr
    Consolidation_Purpose: Purpose
