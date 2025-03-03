from typing import Optional

from fastapi import HTTPException


class LoggedHttpException(HTTPException):
    def __init__(self, log_message: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self._log_message: Optional[str] = log_message

    def get_log_message(self) -> str:
        return f"%s. %s" % (self.detail, self._log_message or "")
