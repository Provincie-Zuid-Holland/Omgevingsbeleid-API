import uuid

from app.extensions.publications.models.api_input_data import ActFrbr
from app.extensions.publications.services.state.actions import Action


class AddWerkingsgebiedAction(Action):
    UUID: uuid.UUID
    Object_ID: int
    Work: str
    Expression_Version: str
    Act_Frbr: ActFrbr
