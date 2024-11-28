import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.attachments.db.tables import StorageFileTable
from app.extensions.attachments.dependencies import depends_storage_file_repository
from app.extensions.attachments.permissions import AttachmentPermissions
from app.extensions.attachments.repository.storage_file_repository import StorageFileRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


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
        original_filename = self._normalize_filename(self._uploaded_file.filename)
        checksum = hashlib.sha256(file_binary).hexdigest()

        file_data: FileData = FileData(
            Binary=file_binary,
            Size=file_size,
            Content_Type=content_type,
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

        file_table: StorageFileTable = StorageFileTable(
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


class AttachmentUploadFileEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            uploaded_file: UploadFile = File(...),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    AttachmentPermissions.can_upload_files,
                )
            ),
            storage_repository: StorageFileRepository = Depends(depends_storage_file_repository),
            db: Session = Depends(depends_db),
            title: str = Form(...),
        ) -> UploadFileResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                storage_repository,
                user,
                uploaded_file,
                title,
            )
            response: UploadFileResponse = handler.handle()
            return response

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            summary=f"Upload an File",
            response_model=UploadFileResponse,
            description=None,
            tags=["Attachments"],
        )

        return router


class AttachmentUploadFileEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "attachment_upload_file"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return AttachmentUploadFileEndpoint(path=path)
