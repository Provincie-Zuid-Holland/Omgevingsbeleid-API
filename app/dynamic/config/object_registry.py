from typing import List
from os import listdir
from os.path import isfile, join
from copy import deepcopy

import yaml

from .models.fields import ObjectField
from .base_fields import base_fields


class ObjectRegistry:
    def __init__(self):
        self._extensions: List[dict] = []
        self._objects: List[dict] = []

        self._base_fields: List[ObjectField] = deepcopy(base_fields)

    def register_extension(self, file_path: str):
        config = self._load_yml(file_path)
        self._extensions.append(config)

    def register_objects(self, dir_path: str):
        file_paths: List[str] = [
            join(dir_path, f) for f in listdir(dir_path) if isfile(join(dir_path, f))
        ]
        for file_path in file_paths:
            self.register_object(file_path)

    def register_object(self, file_path: str):
        config = self._load_yml(file_path)
        self._objects.append(config)
        # id = config["id"]
        # object_type = config["object_type"]

        # relations = relations_loader(config.get("relations", {}))
        # fields = fields_loader(config.get("fields", {}))
        # # models = models_loader(fields, config.get("models", {}))
        # api = ...

        # print("")
        # pprint(fields)
        # print("")

    def build(self):
        pass

    def _load_yml(self, file_path: str) -> dict:
        with open(file_path) as stream:
            return yaml.safe_load(stream)
