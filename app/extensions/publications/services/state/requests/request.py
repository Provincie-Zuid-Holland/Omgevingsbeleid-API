from abc import ABCMeta

from pydantic import BaseModel


class Request(BaseModel, metaclass=ABCMeta):
    pass
