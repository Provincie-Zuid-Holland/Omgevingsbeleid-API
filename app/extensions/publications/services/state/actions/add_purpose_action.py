from datetime import date
from typing import Optional

from app.extensions.publications.enums import PurposeType
from app.extensions.publications.services.state.actions.action import Action


class AddPurposeAction(Action):
    Purpose_Type: PurposeType
    Effective_Date: Optional[date]
    Work_Province_ID: str
    Work_Date: str
    Work_Other: str

    def get_effective_date_str(self) -> str:
        if self.Effective_Date is None:
            return ""

        return self.Effective_Date.strftime("%Y-%m-%d")
