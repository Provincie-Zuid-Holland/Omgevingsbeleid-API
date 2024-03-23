from typing import Dict

from app.extensions.publications.services.state import result_models
from app.extensions.publications.services.state.actions.action import Action


class AddPublicationAction(Action):
    Act_Frbr: result_models.Frbr
    Bill_Frbr: result_models.Frbr
    Consolidation_Purpose: result_models.Purpose
    Document_Type: str
    Procedure_Type: str
    Werkingsgebieden: Dict[int, result_models.Werkingsgebied]
    Wid_Data: result_models.WidData
    Ow_Data: result_models.OwData
