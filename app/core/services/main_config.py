from copy import deepcopy
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class MainConfig:
    def __init__(self, main_config_path: str):
        self._main_config_path: str = main_config_path
        self._main_config: dict = self._load_yaml(main_config_path)

    def get_as_model(self, key: str, response_type: type[T]) -> T:
        value = self._get_element_or_fail(key)
        return response_type.model_validate(value)

    def _get_element_or_fail(self, key: str) -> Any:
        keys: list[str] = key.split(".")
        current: dict = self._main_config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                raise RuntimeError(f"Key '{key}' not found in main config")
        return current

    def get_main_config(self) -> dict:
        return deepcopy(self._main_config)

    def _load_yaml(self, file_path: str) -> dict:
        with open(file_path, "r") as stream:
            return yaml.safe_load(stream)
