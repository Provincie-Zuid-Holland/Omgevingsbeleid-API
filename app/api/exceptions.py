from typing import Optional

from fastapi import HTTPException


class LoggedHttpException(HTTPException):
    def __init__(self, log_message: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_message: Optional[str] = log_message

    def get_log_message(self) -> str:
        return "%s. %s" % (self.detail, self._log_message or "")
