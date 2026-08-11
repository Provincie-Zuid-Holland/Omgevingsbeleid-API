
from fastapi import HTTPException


class LoggedHttpException(HTTPException):
    def __init__(self, log_message: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_message: str | None = log_message

    def get_log_message(self) -> str:
        return "%s. %s" % (self.detail, self._log_message or "")
