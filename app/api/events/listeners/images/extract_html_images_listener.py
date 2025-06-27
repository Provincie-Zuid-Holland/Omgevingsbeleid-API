import base64
import io
import json
import re
import sys
from hashlib import sha256
from typing import List, Optional, Set
from uuid import uuid4

from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.asset_repository import AssetRepository
from app.api.events.listeners.images.types import ImageMeta
from app.api.events.module_object_patched_event import ModuleObjectPatchedEvent
from app.core.services.event.types import Listener
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.others import AssetsTable
from app.core.types import DynamicObjectModel, Model


class ExtractHtmlImagesConfig(BaseModel):
    fields: Set[str]


class HtmlImagesExtractor:
    def __init__(
        self,
        asset_repository: AssetRepository,
        db: Session,
        event: ModuleObjectPatchedEvent,
        config: ExtractHtmlImagesConfig,
        interested_fields: Set[str],
    ):
        self._asset_repository: AssetRepository = asset_repository
        self._db: Session = db
        self._config: ExtractHtmlImagesConfig = config
        self._interested_fields: Set[str] = interested_fields
        self._module_object: ModuleObjectsTable = event.payload.new_record

    def process(self) -> ModuleObjectsTable:
        for field_name in self._interested_fields:
            content: str = getattr(self._module_object, field_name)
            try:
                soup = BeautifulSoup(content, "html.parser")
            except:
                continue

            for img in soup.find_all("img", src=re.compile("^data:image/")):
                self._handle_image(img)
            setattr(self._module_object, field_name, str(soup))

        return self._module_object

    def _handle_image(self, img):
        image_table: AssetsTable = self._get_or_create_asset(img)
        img["src"] = f"[ASSET:{image_table.UUID}]"

    def _get_or_create_asset(self, img) -> AssetsTable:
        # Extract the image data and file extension
        image_data = img["src"]

        match = re.match(r"data:image/(.*?);base64,(.*)", image_data)
        if not match:
            raise ValueError("Invalid data URL")

        # Extract the MIME type and data from the data URL
        mime_type, base64_data = match.groups()
        if mime_type not in ["png", "jpg", "jpeg"]:
            raise ValueError("Invalid mime type for image")

        # First check if the image already exists
        # if so; then we do not need to parse the image to gain the meta
        image_hash: str = sha256(image_data.encode("utf-8")).hexdigest()
        image_table: Optional[AssetsTable] = self._asset_repository.get_by_hash_and_content(image_hash, image_data)
        if image_table is not None:
            return image_table

        picture_data = base64.b64decode(base64_data)
        size = sys.getsizeof(picture_data)
        try:
            image = Image.open(io.BytesIO(picture_data))
        except UnidentifiedImageError:
            raise ValueError("Invalid image")
        width, height = image.size

        meta = ImageMeta(
            ext=f"{image.format}".lower(),
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


class HtmlImagesExtractorFactory:
    def __init__(self, asset_repository: AssetRepository, db: Session):
        self._asset_repository: AssetRepository = asset_repository
        self._db: Session = db

    def create(
        self,
        event: ModuleObjectPatchedEvent,
        config: ExtractHtmlImagesConfig,
        interested_fields: Set[str],
    ) -> HtmlImagesExtractor:
        return HtmlImagesExtractor(
            self._asset_repository,
            self._db,
            event,
            config,
            interested_fields,
        )


class ExtractHtmlImagesListener(Listener[ModuleObjectPatchedEvent]):
    def __init__(self, extractor_factory: HtmlImagesExtractorFactory):
        self._extractor_factory: HtmlImagesExtractorFactory = extractor_factory

    def handle_event(self, event: ModuleObjectPatchedEvent) -> Optional[ModuleObjectPatchedEvent]:
        config: Optional[ExtractHtmlImagesConfig] = self._collect_config(event.context.request_model)
        if not config:
            return event

        changed_fields: Set[str] = set(event.context.changes.keys())
        interested_fields: Set[str] = set.intersection(config.fields, changed_fields)
        if not interested_fields:
            return event

        extractor: HtmlImagesExtractor = self._extractor_factory.create(event, config, interested_fields)
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
                raise RuntimeError("Invalid extract_assets config, expect `fields` to be a list of strings")
            fields.append(field)
        if not fields:
            return None

        config: ExtractHtmlImagesConfig = ExtractHtmlImagesConfig(fields=set(fields))
        return config
