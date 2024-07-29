from app.extensions.publications.services.state import active
from app.extensions.publications.services.state.actions.action import Action


class AddAnnouncementAction(Action):
    Doc_Frbr: active.Frbr
    About_Act_Frbr: active.Frbr
    About_Bill_Frbr: active.Frbr
    Document_Type: str
    Procedure_Type: str
