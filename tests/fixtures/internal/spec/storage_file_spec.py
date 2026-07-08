import hashlib
import mimetypes
from pathlib import Path
import re
from typing import Optional, Sequence
import uuid

from pydantic import Field

from app.core.db.base import Base
from app.core.tables.others import StorageFileTable
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

from datetime import datetime
from typing import ClassVar, Set


from tests.fixtures.internal.types import (
    Link,
)


STORAGE_FILES_DIR: Path = BASE_FILES_DIR / "storage_files"


class StorageFileSpec(Spec):
    __link_fields__: ClassVar[Set[str]] = {"Created_By_UUID"}

    UUID: Optional[uuid.UUID] = None
    Created_Date: Optional[datetime] = None
    Created_By_UUID: Optional[Link] = None
    File_Path: str

    # These will be filled if you just set File_Path
    Lookup: str = ""
    Checksum: str = ""
    Filename: str = ""
    Content_Type: str = ""
    Size: int = 0
    Binary: bytes = Field(default_factory=bytes)

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.UUID, "UUID is not set which is expected to happen at this stage."
        return self.UUID

    def __rich_repr__(self):
        for name, value in self:
            if name == "Binary" and isinstance(value, bytes) and len(value) > 10:
                yield name, value[:20] + b"..."
            else:
                yield name, value


class StorageFilePrefillHandler(BasePrefillHandler[StorageFileSpec]):
    def fill(self, record: Record[StorageFileSpec], context: PrefillContext) -> Record[StorageFileSpec]:
        record = super().fill(record, context)

        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid5(UUID_NAMESPACE, record.spec.File_Path)

        # Process the image
        path = Path(STORAGE_FILES_DIR / record.spec.File_Path)
        content_type: str = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        binary = path.read_bytes()
        checksum = hashlib.sha256(binary).hexdigest()

        record.spec.Lookup = checksum[:10]
        record.spec.Checksum = checksum
        record.spec.Filename = self._normalize_filename(path.name)
        record.spec.Content_Type = content_type
        record.spec.Size = len(binary)
        record.spec.Binary = binary

        return record

    def _normalize_filename(self, name: str) -> str:
        name = name.lower()
        name = re.sub(r"[^a-z0-9.]", "-", name)
        name = re.sub(r"-+", "-", name)
        return name.strip("-")


class StorageFilePersistHandler(BasePersistHandler[StorageFileSpec]):
    def to_rows(self, record: Record[StorageFileSpec], context: PersistContext) -> Sequence[Base]:
        spec: StorageFileSpec = record.spec
        return [
            StorageFileTable(
                UUID=spec.UUID,
                Lookup=spec.Lookup,
                Checksum=spec.Checksum,
                Filename=spec.Filename,
                Content_Type=spec.Content_Type,
                Size=spec.Size,
                Binary=spec.Binary,
                Created_Date=spec.Created_Date,
                Created_By_UUID=spec.Created_By_UUID,
            )
        ]
