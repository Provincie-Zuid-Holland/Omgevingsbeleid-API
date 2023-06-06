from typing import List, Optional, Set
from dataclasses import dataclass
from uuid import UUID
import json
from pydantic import BaseModel

from sqlalchemy.orm import Session
from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent

from app.dynamic.event.types import Listener
from app.dynamic.config.models import Model, DynamicObjectModel
from app.extensions.html_assets.db.tables import AssetsTable
from app.extensions.html_assets.models.meta import ImageMeta
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.modules.event.retrieved_module_objects_event import (
    RetrievedModuleObjectsEvent,
)


@dataclass
class GetImagesConfig:
    fields: Set[str]


class ImageInserter:
    def __init__(
        self,
        event: RetrievedModuleObjectsEvent,
        config: GetImagesConfig,
    ):
        self._config: GetImagesConfig = config
        self._rows: List[BaseModel] = event.payload.rows
        self._db: Session = event.get_db()
        self._asset_repository: AssetRepository = AssetRepository(self._db)

    def process(self) -> List[BaseModel]:
        for index, row in enumerate(self._rows):
            for field_name in self._config.fields:
                if not hasattr(row, field_name):
                    continue

                content: str = getattr(row, field_name)
                if not content:
                    continue

                try:
                    image_uuid = UUID(content)
                except:
                    continue

                asset: Optional[AssetsTable] = self._asset_repository.get_by_uuid(
                    image_uuid
                )
                if not asset:
                    continue

                try:
                    meta_dict: dict = json.loads(asset.Meta)
                    meta: ImageMeta = ImageMeta.parse_obj(meta_dict)
                except:
                    continue

                setattr(row, field_name, asset.Content)

        return self._rows


class GetImagesForModuleListener(Listener[RetrievedModuleObjectsEvent]):
    def handle_event(
        self, event: RetrievedModuleObjectsEvent
    ) -> RetrievedModuleObjectsEvent:
        config: Optional[GetImagesConfig] = self._collect_config(
            event.context.response_model
        )
        if not config:
            return event
        if not config.fields:
            return event

        inserter: ImageInserter = ImageInserter(event, config)
        result_rows = inserter.process()

        event.payload.rows = result_rows
        return event

    def _collect_config(self, request_model: Model) -> Optional[GetImagesConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "get_image" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("get_image", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError(
                    "Invalid get_image config, expect `fields` to be a list of strings"
                )
            fields.append(field)
        if not fields:
            return None

        config: GetImagesConfig = GetImagesConfig(fields=set(fields))
        return config


class GetImagesForObjectListener(Listener[RetrievedObjectsEvent]):
    def handle_event(self, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent:
        config: Optional[GetImagesConfig] = self._collect_config(
            event.context.response_model
        )
        if not config:
            return event
        if not config.fields:
            return event

        inserter: ImageInserter = ImageInserter(event, config)
        result_rows = inserter.process()

        event.payload.rows = result_rows
        return event

    def _collect_config(self, request_model: Model) -> Optional[GetImagesConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "get_image" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("get_image", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError(
                    "Invalid get_image config, expect `fields` to be a list of strings"
                )
            fields.append(field)
        if not fields:
            return None

        config: GetImagesConfig = GetImagesConfig(fields=set(fields))
        return config
