from typing import Dict, List, Tuple

from app.build.services.validators.types import PydanticValidator, Validator


class ValidatorProvider:
    def __init__(self, validators: List[Validator]):
        self._validators: Dict[str, Validator] = {v.get_id(): v for v in validators}
        self._unique_counter: int = 0

    def get(self, validator_id: str, config: dict) -> Tuple[int, PydanticValidator]:
        if validator_id not in self._validators:
            raise RuntimeError(f"Validator ID: '{validator_id}' not found")

        self._unique_counter += 1
        pydantic_validator: PydanticValidator = self._validators[validator_id].get_validator_func(config)

        return self._unique_counter, pydantic_validator
