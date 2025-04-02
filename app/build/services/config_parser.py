from copy import deepcopy
from os import listdir
from os.path import isfile, join
from typing import Dict, List
import yaml

from app.build.objects.types import BuildData, IntermediateObject
from app.build.objects.columns import BASE_COLUMNS
from app.build.services.object_intermediate_builder import ObjectIntermediateBuilder
from app.core.types import Column


class ConfigParser:
    def __init__(self, object_intermediate_builder: ObjectIntermediateBuilder):
        self._object_intermediate_builder: ObjectIntermediateBuilder = object_intermediate_builder

    def parse(self, main_config_path: str, object_config_path: str):
        main_config: dict = self._load_yaml(main_config_path)
        object_configs: List[dict] = self._load_object_configs(object_config_path)
        columns: Dict[str, Column] = self._gather_columns(main_config)
        object_intermediates: List[IntermediateObject] = self._object_intermediate_builder.build(
            columns,
            object_configs,
        )

        return BuildData(
            main_config=main_config,
            object_configs=object_configs,
            columns=columns,
            object_intermediates=object_intermediates,
        )

    def _load_yaml(self, file_path: str) -> dict:
        with open(file_path, "r") as stream:
            return yaml.safe_load(stream)

    def _load_object_configs(self, object_config_path: str) -> List[dict]:
        object_configs: List[dict] = []

        file_paths: List[str] = [
            join(object_config_path, f)
            for f in listdir(object_config_path)
            if isfile(join(object_config_path, f)) and f[0:1] != "_"
        ]

        for file_path in file_paths:
            object_config: dict = self._load_yaml(file_path)
            object_configs.append(object_config)
        
        return object_configs

    def _gather_columns(self, main_config: dict) -> Dict[str, Column]:
        columns: Dict[str, Column] = {
            c.id: c for c in deepcopy(BASE_COLUMNS)
        }

        config_columns = main_config.get("columns", [])
        for column_id, data in config_columns.items():
            if column_id in columns:
                raise RuntimeError(f"Column ID: '{column_id}' already exists")

            columns[column_id] = Column(
                id=column_id,
                name=data["name"],
                type=data["type"],
                type_data=data.get("type_data", {}),
                nullable=data.get("nullable", False),
                static=data.get("static", False),
                serializers=data.get("serializers", []),
                deserializers=data.get("deserializers", []),
            )

        return columns
