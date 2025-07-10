import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.others.repositories.storage_file_repository import StorageFileRepository
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.tables.others import StorageFileTable
from app.core.tables.users import UsersTable


class UploadFileResponse(BaseModel):
    UUID: uuid.UUID


class FileData(BaseModel):
    Binary: bytes
    Size: int
    Content_Type: str
    Filename: str
    Checksum: str

    def get_lookup(self) -> str:
        return self.Checksum[0:10]


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        storage_repository: StorageFileRepository,
        user: UsersTable,
        uploaded_file: UploadFile,
        title: str,
    ):
        self._db: Session = db
        self._storage_repository: StorageFileRepository = storage_repository
        self._user: UsersTable = user
        self._uploaded_file: UploadFile = uploaded_file
        self._title: str = title
        self._timepoint: datetime = datetime.now(timezone.utc)

    def handle(self) -> UploadFileResponse:
        self._guard_upload()

        file_binary = self._uploaded_file.file.read()
        file_size = len(file_binary)
        content_type = self._uploaded_file.content_type
        original_filename = self._normalize_filename(self._uploaded_file.filename or "")
        checksum = hashlib.sha256(file_binary).hexdigest()

        file_data: FileData = FileData(
            Binary=file_binary,
            Size=file_size,
            Content_Type=content_type or "",
            Filename=original_filename,
            Checksum=checksum,
        )

        file_table: StorageFileTable = self._store_file(file_data)
        self._db.commit()
        self._db.flush()

        response: UploadFileResponse = UploadFileResponse(
            UUID=file_table.UUID,
        )
        return response

    def _guard_upload(self):
        if self._uploaded_file.file is None or self._uploaded_file.filename is None:
            raise HTTPException(status_code=400, detail="No file uploaded.")

        if self._uploaded_file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Unsupported file type, expected a PDF.")

    def _normalize_filename(self, filename: str) -> str:
        filename = filename.lower()
        filename = re.sub(r"[^a-z0-9\.]+", "-", filename)
        filename = re.sub(r"-+", "-", filename)
        filename = filename.strip("-")

        return filename

    def _store_file(self, file_data: FileData) -> StorageFileTable:
        existing_file_table: Optional[StorageFileTable] = self._storage_repository.get_by_checksum_uuid(
            file_data.Checksum
        )
        if existing_file_table is not None:
            return existing_file_table

        file_table = StorageFileTable(
            UUID=uuid.uuid4(),
            Lookup=file_data.get_lookup(),
            Checksum=file_data.Checksum,
            Filename=file_data.Filename,
            Content_Type=file_data.Content_Type,
            Size=file_data.Size,
            Binary=file_data.Binary,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        self._db.add(file_table)
        self._db.flush()
        return file_table


@inject
def post_files_upload_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    storage_repository: Annotated[StorageFileRepository, Depends(Provide[ApiContainer.storage_file_repository])],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    title: str = Form(...),
    uploaded_file: UploadFile = File(...),
) -> UploadFileResponse:
    permission_service.guard_valid_user(Permissions.storage_file_can_upload_files, user)

    handler: EndpointHandler = EndpointHandler(
        db,
        storage_repository,
        user,
        uploaded_file,
        title,
    )
    response: UploadFileResponse = handler.handle()
    return response
