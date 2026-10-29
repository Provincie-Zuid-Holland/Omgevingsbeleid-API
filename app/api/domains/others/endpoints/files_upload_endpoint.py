import uuid
from datetime import UTC, datetime
from typing import Annotated

import anyio
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.others.repositories.storage_file_repository import StorageFileRepository
from app.api.domains.others.services import PdfMetaService
from app.api.domains.others.types import FileData
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.tables.others import StorageFileTable
from app.core.tables.users import UsersTable


class UploadFileResponse(BaseModel):
    id: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        session: AsyncSession,
        storage_repository: StorageFileRepository,
        pdf_meta_service: PdfMetaService,
        user: UsersTable,
        uploaded_file: UploadFile,
        title: str,
        ignore_report: bool,
    ):
        self._session: AsyncSession = session
        self._storage_repository: StorageFileRepository = storage_repository
        self._pdf_meta_service: PdfMetaService = pdf_meta_service
        self._user: UsersTable = user
        self._uploaded_file: UploadFile = uploaded_file
        self._title: str = title
        self._ignore_report: bool = ignore_report
        self._timepoint: datetime = datetime.now(UTC)

    async def handle(self) -> UploadFileResponse:
        self._file_data: FileData = FileData(file_in=self._uploaded_file, binary=await self._uploaded_file.read())
        self._guard_upload()

        if not self._ignore_report:
            pdf_meta_report = await anyio.to_thread.run_sync(
                self._pdf_meta_service.report_banned_meta, self._file_data.get_binary()
            )
            if len(pdf_meta_report) > 0:
                raise HTTPException(434, detail=jsonable_encoder(pdf_meta_report))

        file_table: StorageFileTable = await self._store_file()
        await self._session.flush()
        await self._session.commit()

        response: UploadFileResponse = UploadFileResponse(
            id=file_table.id,
        )
        return response

    def _guard_upload(self):
        if self._uploaded_file.file is None or self._uploaded_file.filename is None:
            raise HTTPException(status_code=400, detail="No file uploaded.")

        if self._uploaded_file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Unsupported file type, expected a PDF.")

    async def _store_file(self) -> StorageFileTable:
        existing_file_table: StorageFileTable | None = await self._storage_repository.get_by_checksum_uuid(
            self._session,
            self._file_data.get_checksum(),
        )
        if existing_file_table is not None:
            return existing_file_table

        file_table = StorageFileTable(
            id=uuid.uuid4(),
            lookup=self._file_data.get_lookup(),
            checksum=self._file_data.get_checksum(),
            filename=self._file_data.normalize_filename(),
            content_type=self._file_data.get_content_type(),
            size=self._file_data.get_size(),
            binary=self._file_data.get_binary(),
            created_date=self._timepoint,
            created_by_id=self._user.id,
        )
        self._session.add(file_table)
        await self._session.flush()
        return file_table


@inject
async def post_files_upload_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    storage_repository: Annotated[StorageFileRepository, Depends(Provide[ApiContainer.storage_file_repository])],
    session: Annotated[AsyncSession, Depends(depends_db_session)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    pdf_meta_service: Annotated[PdfMetaService, Depends(Provide[ApiContainer.pdf_meta_service])],
    title: Annotated[str, Form()],
    ignore_report: Annotated[bool, Form()],
    uploaded_file: Annotated[UploadFile, File()],
) -> UploadFileResponse:
    permission_service.guard_valid_user(Permissions.storage_file_can_upload_files, user)

    handler: EndpointHandler = EndpointHandler(
        session,
        storage_repository,
        pdf_meta_service,
        user,
        uploaded_file,
        title,
        ignore_report,
    )
    response: UploadFileResponse = await handler.handle()
    return response
