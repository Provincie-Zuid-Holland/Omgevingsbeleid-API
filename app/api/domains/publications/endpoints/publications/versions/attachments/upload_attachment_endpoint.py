import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, File, Form, HTTPException, UploadFile, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.others.services import PdfMetaService
from app.api.domains.others.types import FileData
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


@inject
def post_upload_attachment_endpoint(
    version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_version,
            )
        ),
    ],
    storage_file_repository: Annotated[
        PublicationStorageFileRepository, Depends(Provide[ApiContainer.publication.storage_file_repository])
    ],
    pdf_meta_service: Annotated[PdfMetaService, Depends(Provide[ApiContainer.pdf_meta_service])],
    session: Annotated[Session, Depends(depends_db_session)],
    title: str = Form(...),
    uploaded_file: UploadFile = File(...),
    ignore_report: bool = Form(...),
) -> UploadAttachmentResponse:
    _guard_upload(version, uploaded_file)

    file_data: FileData = FileData(
        File=uploaded_file,
    )

    if not ignore_report:
        pdf_meta_report = pdf_meta_service.report_banned_meta(file_data.get_binary())
        if len(pdf_meta_report) > 0:
            raise HTTPException(434, detail=jsonable_encoder(pdf_meta_report))

    timepoint: datetime = datetime.now(timezone.utc)

    file_table: PublicationStorageFileTable = _store_file(
        session,
        storage_file_repository,
        timepoint,
        user.UUID,
        file_data,
    )
    session.add(file_table)
    session.flush()

    attachment = PublicationVersionAttachmentTable(
        Publication_Version_UUID=version.UUID,
        File_UUID=file_table.UUID,
        Filename=file_data.normalize_filename(),
        Title=title,
        Created_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_Date=timepoint,
        Modified_By_UUID=user.UUID,
    )
    session.add(attachment)
    session.commit()
    session.flush()

    response: UploadAttachmentResponse = UploadAttachmentResponse(ID=attachment.ID)
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


def _store_file(
    session: Session,
    repository: PublicationStorageFileRepository,
    timepoint: datetime,
    user_uuid: uuid.UUID,
    file_data: FileData,
) -> PublicationStorageFileTable:
    existing_file_table: Optional[PublicationStorageFileTable] = repository.get_by_checksum_uuid(
        session,
        file_data.get_checksum(),
    )
    if existing_file_table is not None:
        return existing_file_table

    file_table: PublicationStorageFileTable = PublicationStorageFileTable(
        UUID=uuid.uuid4(),
        Lookup=file_data.get_lookup(),
        Checksum=file_data.get_checksum(),
        Filename=file_data.normalize_filename(),
        Content_Type=file_data.get_content_type() or "",
        Size=file_data.get_size(),
        Binary=file_data.get_binary(),
        Created_Date=timepoint,
        Created_By_UUID=user_uuid,
    )
    return file_table
