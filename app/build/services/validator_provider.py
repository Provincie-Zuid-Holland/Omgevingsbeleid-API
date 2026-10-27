from app.build.services.validators.types import AsyncValidator, PydanticValidator, Validator


class ValidatorProvider:
    def __init__(self, validators: list[Validator]):
        self._validators: dict[str, Validator] = {v.get_id(): v for v in validators}
        self._unique_counter: int = 0

    def get(self, validator_id: str, config: dict) -> tuple[int, PydanticValidator | AsyncValidator]:
        if validator_id not in self._validators:
            raise RuntimeError(f"Validator ID: '{validator_id}' not found")

        self._unique_counter += 1
        validator: PydanticValidator | AsyncValidator = self._validators[validator_id].get_validator_func(config)

        return self._unique_counter, validator
