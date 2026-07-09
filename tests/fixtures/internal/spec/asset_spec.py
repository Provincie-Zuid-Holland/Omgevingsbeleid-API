import base64
from hashlib import sha256
import json
import mimetypes
from pathlib import Path
from typing import Optional, Sequence
import uuid


from app.core.db.base import Base
from app.core.tables.others import AssetsTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    Spec,
    Record,
    UUID_NAMESPACE,
    PrimaryKey,
    PersistContext,
    BasePersistHandler,
    BASE_FILES_DIR,
)
from PIL import Image

from datetime import datetime
from typing import ClassVar, Set


from tests.fixtures.internal.types import (
    Link,
)


ASSETS_DIR: Path = BASE_FILES_DIR / "assets"


class AssetSpec(Spec):
    __link_fields__: ClassVar[Set[str]] = {"Created_By_UUID"}

    UUID: Optional[uuid.UUID] = None
    Created_Date: Optional[datetime] = None
    Created_By_UUID: Optional[Link] = None
    File_Path: str

    # These will be filled if you just set File_Path
    Lookup: str = ""
    Hash: str = ""
    Meta: str = ""
    Content: str = ""

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.UUID, "UUID is not set which is expected to happen at this stage."
        return self.UUID


class AssetPrefillHandler(BasePrefillHandler[AssetSpec]):
    def fill(self, record: Record[AssetSpec], context: PrefillContext) -> Record[AssetSpec]:
        record = super().fill(record, context)

        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid5(UUID_NAMESPACE, record.spec.File_Path)

        # Process the image
        path = Path(ASSETS_DIR / record.spec.File_Path)
        image_raw: bytes = path.read_bytes()

        with Image.open(path) as img:
            width, height = img.size

        mime: str = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        b64: str = base64.b64encode(image_raw).decode("ascii")
        content: str = f"data:{mime};base64,{b64}"

        record.spec.Content = content
        record.spec.Hash = sha256(image_raw).hexdigest()
        record.spec.Lookup = record.spec.Hash[:10]
        record.spec.Meta = json.dumps(
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
                UUID=spec.UUID,
                Created_Date=spec.Created_Date,
                Created_By_UUID=spec.Created_By_UUID,
                Lookup=spec.Lookup,
                Hash=spec.Hash,
                Meta=spec.Meta,
                Content=spec.Content,
            )
        ]
