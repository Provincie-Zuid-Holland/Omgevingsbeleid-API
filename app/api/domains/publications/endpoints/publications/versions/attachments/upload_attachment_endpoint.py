import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.publications.dependencies import depends_publication_version
from app.api.domains.publications.repository.publication_storage_file_repository import PublicationStorageFileRepository
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import (
    PublicationStorageFileTable,
    PublicationVersionAttachmentTable,
    PublicationVersionTable,
)
from app.core.tables.users import UsersTable


class UploadAttachmentResponse(BaseModel):
    ID: int


class FileData(BaseModel):
    Binary: bytes
    Size: int
    Content_Type: str
    Filename: str
    Checksum: str

    def get_lookup(self) -> str:
        return self.Checksum[0:10]


@inject
def post_upload_attachment_endpoint(
    version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    uploaded_file: Annotated[UploadFile, Depends(File(...))],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_version,
            )
        ),
    ],
    storage_repository: Annotated[
        PublicationStorageFileRepository, Depends(Provide[ApiContainer.publication.storage_file_repository])
    ],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    title: Annotated[str, Depends(Form(...))],
) -> UploadAttachmentResponse:
    _guard_upload(version, uploaded_file)
    timepoint: datetime = datetime.now(timezone.utc)

    file_binary = uploaded_file.file.read()
    file_size = len(file_binary)
    content_type = uploaded_file.content_type
    original_filename = _normalize_filename(uploaded_file.filename)
    checksum = hashlib.sha256(file_binary).hexdigest()

    file_data: FileData = FileData(
        Binary=file_binary,
        Size=file_size,
        Content_Type=content_type or "",
        Filename=original_filename,
        Checksum=checksum,
    )
    file_table: PublicationStorageFileTable = _store_file(storage_repository, timepoint, user.UUID, file_data)
    db.add(file_table)
    db.flush()

    attachment = PublicationVersionAttachmentTable(
        Publication_Version_UUID=version.UUID,
        File_UUID=file_table.UUID,
        Filename=original_filename,
        Title=title,
        Created_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_Date=timepoint,
        Modified_By_UUID=user.UUID,
    )
    db.add(attachment)
    db.commit()
    db.flush()

    response: UploadAttachmentResponse = UploadAttachmentResponse(
        ID=attachment.ID,
    )
    return response


def _guard_upload(version: PublicationVersionTable, uploaded_file: UploadFile):
    if not version.Publication.Act.Is_Active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This act can no longer be used")
    if version.Is_Locked:
        raise HTTPException(status.HTTP_409_CONFLICT, "This publication version is locked")
    if uploaded_file.file is None or uploaded_file.filename is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No file uploaded.")
    if uploaded_file.content_type != "application/pdf":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported file type, expected a PDF.")


def _normalize_filename(filename: Optional[str]) -> str:
    if filename is None:
        return "file.pdf"
    filename = filename.lower()
    filename = re.sub(r"[^a-z0-9\.]+", "-", filename)
    filename = re.sub(r"-+", "-", filename)
    filename = filename.strip("-")
    return filename


def _store_file(
    repository: PublicationStorageFileRepository,
    timepoint: datetime,
    user_uuid: uuid.UUID,
    file_data: FileData,
) -> PublicationStorageFileTable:
    existing_file_table: Optional[PublicationStorageFileTable] = repository.get_by_checksum_uuid(
        file_data.Checksum,
    )
    if existing_file_table is not None:
        return existing_file_table

    file_table: PublicationStorageFileTable = PublicationStorageFileTable(
        UUID=uuid.uuid4(),
        Lookup=file_data.get_lookup(),
        Checksum=file_data.Checksum,
        Filename=file_data.Filename,
        Content_Type=file_data.Content_Type,
        Size=file_data.Size,
        Binary=file_data.Binary,
        Created_Date=timepoint,
        Created_By_UUID=user_uuid,
    )
    return file_table
