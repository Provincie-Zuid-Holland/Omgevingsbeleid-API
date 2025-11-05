from copy import deepcopy
from typing import Any

import yaml


class MainConfig:
    def __init__(self, main_config_path: str):
        self._main_config_path: str = main_config_path
        self._main_config: dict = self._load_yaml(main_config_path)

    def get_element_or_fail(self, key: str) -> Any:
        keys = key.split(".")
        current = self._main_config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                raise RuntimeError(f"Key '{key}' not found in main config (at '{k}')")
        return current

    def get_main_config(self) -> dict:
        return deepcopy(self._main_config)

    def _load_yaml(self, file_path: str) -> dict:
        with open(file_path, "r") as stream:
            return yaml.safe_load(stream)
