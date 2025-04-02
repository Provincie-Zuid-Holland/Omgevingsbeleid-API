from typing import Dict

from app.dynamic.validators.validator import Validator


class ValidatorProvider:
    def __init__(self):
        self._validators: Dict[str, Validator] = {}

    def register(self, validator: Validator):
        id: str = validator.get_id()
        if id in self._validators:
            raise RuntimeError(f"Validator with id `{id}` has already been registered")

        self._validators[id] = validator

    def get_validator(self, id: str, config: dict):
        if not id in self._validators:
            raise RuntimeError(f"Validator with id `{id}` does not exist")

        return self._validators[id].get_validator_func(config)
