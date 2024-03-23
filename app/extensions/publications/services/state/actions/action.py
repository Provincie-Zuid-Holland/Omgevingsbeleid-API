from abc import ABCMeta

from pydantic import BaseModel


class Action(BaseModel, metaclass=ABCMeta):
    pass
