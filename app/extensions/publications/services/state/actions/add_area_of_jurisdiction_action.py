import uuid

from app.extensions.publications.models.api_input_data import ActFrbr
from app.extensions.publications.services.state.actions.action import Action


class AddAreaOfJurisdictionAction(Action):
    UUID: uuid.UUID
    Administrative_Borders_ID: str
    Act_Frbr: ActFrbr
