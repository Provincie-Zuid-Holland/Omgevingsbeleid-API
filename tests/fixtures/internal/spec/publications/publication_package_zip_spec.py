import hashlib
import io
import uuid
import zipfile
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from pydantic import Field

from app.core.db.base import Base
from app.core.tables.publications import PublicationPackageZipTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import (
    BASE_FILES_DIR,
    DATETIME_T0,
    BasePersistHandler,
    Link,
    PersistContext,
    PrimaryKey,
    Record,
    Spec,
)

FILES_DIR: Path = BASE_FILES_DIR / "publication_package_zips"


class PublicationPackageZipSpec(Spec):
    __link_fields__: ClassVar[set[str]] = {"created_by_id", "latest_download_by_id"}

    id: uuid.UUID | None = None
    created_date: datetime | None = None
    created_by_id: Link | None = None
    file_path: str

    filename: str = ""
    checksum: str = ""
    binary: bytes = Field(default_factory=bytes)

    latest_download_date: datetime | None = None
    latest_download_by_id: Link | None = None

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "`id` is not set which is expected to happen at this stage."
        return self.id

    def __rich_repr__(self):
        for name, value in self:
            if name == "binary" and isinstance(value, bytes) and len(value) > 10:
                yield name, value[:20] + b"..."
            else:
                yield name, value


class PublicationPackageZipPrefillHandler(BasePrefillHandler[PublicationPackageZipSpec]):
    def fill(
        self, record: Record[PublicationPackageZipSpec], context: PrefillContext
    ) -> Record[PublicationPackageZipSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid4()

        path: Path = Path(FILES_DIR / record.spec.file_path)
        assert path.is_dir(), f"`{path}` is expected to be a directory with the zip contents."
        binary: bytes = self._zip_directory(path)

        record.spec.filename = record.spec.filename or f"{path.name}.zip"
        record.spec.checksum = hashlib.sha256(binary).hexdigest()
        record.spec.binary = binary

        return record

    def _zip_directory(self, path: Path) -> bytes:
        files: list[Path] = sorted(file for file in path.rglob("*") if file.is_file())
        assert files, f"`{path}` does not contain any files."

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                info = zipfile.ZipInfo(file.relative_to(path).as_posix(), date_time=DATETIME_T0.timetuple()[:6])
                info.compress_type = zipfile.ZIP_DEFLATED
                zip_file.writestr(info, file.read_bytes())
        return buffer.getvalue()


class PublicationPackageZipPersistHandler(BasePersistHandler[PublicationPackageZipSpec]):
    def to_rows(self, record: Record[PublicationPackageZipSpec], context: PersistContext) -> Sequence[Base]:
        spec: PublicationPackageZipSpec = record.spec
        return [
            PublicationPackageZipTable(
                id=spec.id,
                filename=spec.filename,
                binary=spec.binary,
                checksum=spec.checksum,
                latest_download_date=spec.latest_download_date,
                latest_download_by_id=spec.latest_download_by_id,
                created_date=spec.created_date,
                created_by_id=spec.created_by_id,
            )
        ]
