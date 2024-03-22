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

    def __repr__(self) -> str:
        return f"""
        class AddPurposeAction(
            Purpose_Type="{self.Purpose_Type.value}",
            Effective_Date="{self.get_effective_date_str()}",
            Work_Province_ID="{self.Work_Province_ID}",
            Work_Date="{self.Work_Date}",
            Work_Other="{self.Work_Other}",
        )
        """
