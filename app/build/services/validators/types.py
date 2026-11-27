from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic.functional_validators import FieldValidatorModes
from sqlalchemy.ext.asyncio import AsyncSession

# The pydantic model attribute that holds the model's (field name, AsyncValidator) pairs
ASYNC_VALIDATORS_ATTRIBUTE = "__async_validators__"


# @see: Pydantic.field_validator
@dataclass
class PydanticValidator:
    mode: FieldValidatorModes
    func: Callable


# For validators that need the database. Runs after pydantic validation, with the request session.
@dataclass
class AsyncValidator:
    func: Callable[[AsyncSession, Any, dict], Awaitable[Any]]


class Validator(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def get_validator_func(self, config: dict) -> PydanticValidator | AsyncValidator:
        pass
