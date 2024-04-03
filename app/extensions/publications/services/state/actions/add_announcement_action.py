from app.extensions.publications.services.state import result_models
from app.extensions.publications.services.state.actions.action import Action


class AddAnnouncementAction(Action):
    Doc_Frbr: result_models.Frbr
    About_Act_Frbr: result_models.Frbr
    About_Bill_Frbr: result_models.Frbr
    Document_Type: str
    Procedure_Type: str
    # @todo: add procedure dates
