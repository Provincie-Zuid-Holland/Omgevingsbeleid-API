from typing import Dict

from app.extensions.publications.services.state import active
from app.extensions.publications.services.state.actions.action import Action


class AddPublicationAction(Action):
    Act_Frbr: active.Frbr
    Bill_Frbr: active.Frbr
    Consolidation_Purpose: active.Purpose
    Document_Type: str
    Procedure_Type: str
    Werkingsgebieden: Dict[int, active.Werkingsgebied]
    Wid_Data: active.WidData
    Ow_Data: active.OwData
    Act_Text: str
