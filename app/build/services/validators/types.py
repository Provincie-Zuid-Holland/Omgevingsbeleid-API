from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from pydantic.functional_validators import FieldValidatorModes


# @see: Pydantic.field_validator
@dataclass
class PydanticValidator:
    mode: FieldValidatorModes
    func: Callable


class Validator(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def get_validator_func(self, config: dict) -> PydanticValidator:
        pass
