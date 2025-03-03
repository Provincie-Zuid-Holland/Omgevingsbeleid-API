import functools
from typing import Optional

import dso.exceptions as dso_exceptions


class DSORenvooiException(Exception):
    def __init__(self, message: str, internal_error: Optional[str] = None):
        super().__init__(message)
        self.message: str = message
        self.internal_error: Optional[str] = internal_error


class DSOConfigurationException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def dso_exception_mapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except dso_exceptions.RenvooiXmlError as e:
            raise DSORenvooiException(e.msg, e.msg) from e
        except dso_exceptions.RenvooiUnauthorizedError as e:
            raise DSORenvooiException("Renvooi unauthorized error", e.msg) from e
        except dso_exceptions.RenvooiInternalServerError as e:
            raise DSORenvooiException("Renvooi internal server error", e.msg) from e
        except dso_exceptions.RenvooiUnkownError as e:
            raise DSORenvooiException("Renvooi unknown error", e.msg) from e

    return wrapper
