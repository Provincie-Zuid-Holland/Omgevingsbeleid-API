from dataclasses import dataclass
from hashlib import sha256
import json
from typing import List, Optional, Set
import re
import base64
import sys
import io
from uuid import uuid4

from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.dynamic.config.models import DynamicObjectModel, Model
from app.dynamic.event.types import Listener
from app.extensions.html_assets.db.tables import AssetsTable
from app.extensions.html_assets.models.meta import ImageMeta
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.event.module_object_patched_event import (
    ModuleObjectPatchedEvent,
)


@dataclass
class ExtractHtmlImagesConfig:
    fields: Set[str]


class HtmlImagesExtractor:
    def __init__(
        self,
        event: ModuleObjectPatchedEvent,
        config: ExtractHtmlImagesConfig,
        interested_fields: Set[str],
    ):
        self._config: ExtractHtmlImagesConfig = config
        self._interested_fields: Set[str] = interested_fields
        self._module_object: ModuleObjectsTable = event.payload.new_record
        self._db: Session = event.get_db()
        self._asset_repository: AssetRepository = AssetRepository(self._db)

    def process(self) -> ModuleObjectsTable:
        for field_name in self._interested_fields:
            content: str = getattr(self._module_object, field_name)
            soup = BeautifulSoup(content, "html.parser")
            for img in soup.find_all("img", src=re.compile("^data:image/")):
                self._handle_image(img)
            setattr(self._module_object, field_name, str(soup))

        return self._module_object

    def _handle_image(self, img):
        image_table: AssetsTable = self._get_or_create_asset(img)
        img["src"] = f"[ASSET:{image_table.UUID}]"

    def _get_or_create_asset(self, img) -> AssetsTable:
        # Extract the image data and file extension
        image_data = img["src"].split(",")[1]
        ext = img["src"].split(";")[0].split("/")[1]

        # First check if the image already exists
        # if so; then we do not need to parse the image to gain the meta
        image_hash: str = sha256(image_data.encode("utf-8")).hexdigest()
        image_table: Optional[
            AssetsTable
        ] = self._asset_repository.get_by_hash_and_content(image_hash, image_data)
        if image_table is not None:
            return image_table

        picture_data = base64.b64decode(image_data)
        size = sys.getsizeof(picture_data)
        try:
            image = Image.open(io.BytesIO(picture_data))
        except UnidentifiedImageError:
            raise ValueError("Invalid image")
        width, height = image.size

        meta: ImageMeta = ImageMeta(
            ext=ext,
            width=width,
            height=height,
            size=size,
        )
        image_table = AssetsTable(
            UUID=uuid4(),
            Created_Date=self._module_object.Created_Date,
            Created_By_UUID=self._module_object.Created_By_UUID,
            Lookup=image_hash[0:10],
            Hash=image_hash,
            Meta=json.dumps(meta.to_dict()),
            Content=image_data,
        )
        self._db.add(image_table)
        return image_table


class ExtractHtmlImagesListener(Listener[ModuleObjectPatchedEvent]):
    def handle_event(
        self, event: ModuleObjectPatchedEvent
    ) -> Optional[ModuleObjectPatchedEvent]:
        config: Optional[ExtractHtmlImagesConfig] = self._collect_config(
            event.context.request_model
        )
        if not config:
            return event

        changed_fields: Set[str] = set(event.context.changes.keys())
        interested_fields: Set[str] = set.intersection(config.fields, changed_fields)
        if not interested_fields:
            return event

        extractor: HtmlImagesExtractor = HtmlImagesExtractor(event, config, interested_fields)
        result_object = extractor.process()

        event.payload.new_record = result_object
        return event

    def _collect_config(self, request_model: Model) -> Optional[ExtractHtmlImagesConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "extract_assets" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("extract_assets", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError(
                    "Invalid extract_assets config, expect `fields` to be a list of strings"
                )
            fields.append(field)
        if not fields:
            return None

        config: ExtractHtmlImagesConfig = ExtractHtmlImagesConfig(fields=set(fields))
        return config
