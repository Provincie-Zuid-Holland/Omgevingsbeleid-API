import base64
import json
import mimetypes
import uuid
from collections.abc import Sequence
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import ClassVar

from PIL import Image

from app.core.db.base import Base
from app.core.tables.others import AssetsTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BASE_FILES_DIR,
    UUID_NAMESPACE,
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)

ASSETS_DIR: Path = BASE_FILES_DIR / "assets"


class AssetSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    file_path: str

    # These will be filled if you just set File_Path
    lookup: str = ""
    hash: str = ""
    meta: str = ""
    content: str = ""

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "UUID is not set which is expected to happen at this stage."
        return self.id


class AssetPrefillHandler(BasePrefillHandler[AssetSpec]):
    def fill(self, record: Record[AssetSpec], context: PrefillContext) -> Record[AssetSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid5(UUID_NAMESPACE, record.spec.file_path)

        # Process the image
        path = Path(ASSETS_DIR / record.spec.file_path)
        image_raw: bytes = path.read_bytes()

        with Image.open(path) as img:
            width, height = img.size

        mime: str = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        b64: str = base64.b64encode(image_raw).decode("ascii")
        content: str = f"data:{mime};base64,{b64}"

        record.spec.content = content
        record.spec.hash = sha256(image_raw).hexdigest()
        record.spec.lookup = record.spec.hash[:10]
        record.spec.meta = json.dumps(
            {
                "ext": path.suffix.lstrip("."),
                "width": width,
                "height": height,
                "size": len(image_raw),
            }
        )

        return record


class AssetPersistHandler(BasePersistHandler[AssetSpec]):
    def to_rows(self, record: Record[AssetSpec], context: PersistContext) -> Sequence[Base]:
        spec: AssetSpec = record.spec
        return [
            AssetsTable(
                id=spec.id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
                lookup=spec.lookup,
                hash=spec.hash,
                meta=spec.meta,
                content=spec.content,
            )
        ]
