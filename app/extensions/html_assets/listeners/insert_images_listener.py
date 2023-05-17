from typing import List, Optional, Set
from dataclasses import dataclass
from uuid import UUID
from bs4 import BeautifulSoup
import re
import json
from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.dynamic.event.types import Listener
from app.dynamic.config.models import Model, DynamicObjectModel
from app.extensions.html_assets.db.tables import AssetsTable
from app.extensions.html_assets.models.meta import ImageMeta
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.modules.event.retrieved_module_objects_event import (
    RetrievedModuleObjectsEvent,
)


@dataclass
class InsertHtmlImagesConfig:
    fields: Set[str]


class HtmlImagesInserter:
    def __init__(
        self,
        event: RetrievedModuleObjectsEvent,
        config: InsertHtmlImagesConfig,
    ):
        self._config: InsertHtmlImagesConfig = config
        self._rows: List[BaseModel] = event.payload.rows
        self._db: Session = event.get_db()
        self._asset_repository: AssetRepository = AssetRepository(self._db)

    def process(self) -> List[BaseModel]:
        for index, row in enumerate(self._rows):
            for field_name in self._config.fields:
                if not hasattr(row, field_name):
                    continue

                content: str = getattr(row, field_name)
                try:
                    soup = BeautifulSoup(content, "html.parser")
                except:
                    continue

                for img in soup.find_all("img", src=re.compile("^\[ASSET")):
                    try:
                        asset_uuid = UUID(img["src"].split(":")[1][:-1])
                    except:
                        continue

                    asset: Optional[AssetsTable] = self._asset_repository.get_by_uuid(
                        asset_uuid
                    )
                    if not asset:
                        continue

                    try:
                        meta_dict: dict = json.loads(asset.Meta)
                        meta: ImageMeta = ImageMeta.parse_obj(meta_dict)
                    except:
                        continue
                    img["src"] = asset.Content

                setattr(row, field_name, str(soup))

        return self._rows


class InsertHtmlImagesListener(Listener[RetrievedModuleObjectsEvent]):
    def handle_event(
        self, event: RetrievedModuleObjectsEvent
    ) -> RetrievedModuleObjectsEvent:
        config: Optional[InsertHtmlImagesConfig] = self._collect_config(
            event.context.response_model
        )
        if not config:
            return event
        if not config.fields:
            return event

        inserter: HtmlImagesInserter = HtmlImagesInserter(event, config)
        result_rows = inserter.process()

        event.payload.rows = result_rows
        return event

    def _collect_config(self, request_model: Model) -> Optional[InsertHtmlImagesConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "insert_assets" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("insert_assets", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError(
                    "Invalid insert_assets config, expect `fields` to be a list of strings"
                )
            fields.append(field)
        if not fields:
            return None

        config: InsertHtmlImagesConfig = InsertHtmlImagesConfig(fields=set(fields))
        return config
