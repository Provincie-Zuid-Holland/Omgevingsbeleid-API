import hashlib
import mimetypes
import re
import uuid
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from pydantic import Field

from app.core.db.base import Base
from app.core.tables.others import StorageFileTable
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

STORAGE_FILES_DIR: Path = BASE_FILES_DIR / "storage_files"


class StorageFileSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    file_path: str

    # These will be filled if you just set File_Path
    lookup: str = ""
    checksum: str = ""
    filename: str = ""
    content_type: str = ""
    size: int = 0
    binary: bytes = Field(default_factory=bytes)

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "UUID is not set which is expected to happen at this stage."
        return self.id

    def __rich_repr__(self):
        for name, value in self:
            if name == "binary" and isinstance(value, bytes) and len(value) > 10:
                yield name, value[:20] + b"..."
            else:
                yield name, value


class StorageFilePrefillHandler(BasePrefillHandler[StorageFileSpec]):
    def fill(self, record: Record[StorageFileSpec], context: PrefillContext) -> Record[StorageFileSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid5(UUID_NAMESPACE, record.spec.file_path)

        # Process the image
        path = Path(STORAGE_FILES_DIR / record.spec.file_path)
        content_type: str = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        binary = path.read_bytes()
        checksum = hashlib.sha256(binary).hexdigest()

        record.spec.lookup = checksum[:10]
        record.spec.checksum = checksum
        record.spec.filename = self._normalize_filename(path.name)
        record.spec.content_type = content_type
        record.spec.size = len(binary)
        record.spec.binary = binary

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
                id=spec.id,
                lookup=spec.lookup,
                checksum=spec.checksum,
                filename=spec.filename,
                content_type=spec.content_type,
                size=spec.size,
                binary=spec.binary,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
            )
        ]
