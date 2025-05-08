from copy import deepcopy

import yaml


class MainConfig:
    def __init__(self, main_config_path: str):
        self._main_config_path: str = main_config_path
        self._main_config: dict = self._load_yaml(main_config_path)

    def get_main_config(self) -> dict:
        return deepcopy(self._main_config)

    def _load_yaml(self, file_path: str) -> dict:
        with open(file_path, "r") as stream:
            return yaml.safe_load(stream)
