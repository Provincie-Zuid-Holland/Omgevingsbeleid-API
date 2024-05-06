import hashlib
import re
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import (
    depends_publication_storage_file_repository,
    depends_publication_version,
    depends_publication_version_attachment_repository,
)
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_storage_file_repository import PublicationStorageFileRepository
from app.extensions.publications.repository.publication_version_attachment_repository import (
    PublicationVersionAttachmentRepository,
)
from app.extensions.publications.tables.tables import (
    PublicationStorageFileTable,
    PublicationVersionAttachmentTable,
    PublicationVersionTable,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


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


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        storage_repository: PublicationStorageFileRepository,
        attachment_repository: PublicationVersionAttachmentRepository,
        user: UsersTable,
        uploaded_file: UploadFile,
        version: PublicationVersionTable,
        title: str,
    ):
        self._db: Session = db
        self._storage_repository: PublicationStorageFileRepository = storage_repository
        self._attachment_repository: PublicationVersionAttachmentRepository = attachment_repository
        self._user: UsersTable = user
        self._uploaded_file: UploadFile = uploaded_file
        self._version: PublicationVersionTable = version
        self._title: str = title
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> UploadAttachmentResponse:
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
        file_table: PublicationStorageFileTable = self._store_file(file_data)

        attachment: PublicationVersionAttachmentTable = PublicationVersionAttachmentTable(
            Publication_Version_UUID=self._version.UUID,
            File_UUID=file_table.UUID,
            Filename=original_filename,
            Title=self._title,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_Date=self._timepoint,
            Modified_By_UUID=self._user.UUID,
        )
        self._db.add(attachment)
        self._db.commit()
        self._db.flush()

        response: UploadAttachmentResponse = UploadAttachmentResponse(
            ID=attachment.ID,
        )
        return response

    def _guard_upload(self):
        if self._version.Is_Locked:
            raise HTTPException(status_code=409, detail="This publication version is locked")

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

    def _store_file(self, file_data: FileData) -> PublicationStorageFileTable:
        existing_file_table: Optional[PublicationStorageFileTable] = self._storage_repository.get_by_checksum_uuid(
            file_data.Checksum
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
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        self._db.add(file_table)
        self._db.flush()
        return file_table


class UploadPublicationVersionAttachmentEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            version: PublicationVersionTable = Depends(depends_publication_version),
            uploaded_file: UploadFile = File(...),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_edit_publication_version,
                )
            ),
            storage_repository: PublicationStorageFileRepository = Depends(depends_publication_storage_file_repository),
            attachment_repository: PublicationVersionAttachmentRepository = Depends(
                depends_publication_version_attachment_repository
            ),
            db: Session = Depends(depends_db),
            title: str = Form(...),
        ) -> UploadAttachmentResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                storage_repository,
                attachment_repository,
                user,
                uploaded_file,
                version,
                title,
            )
            response: UploadAttachmentResponse = handler.handle()
            return response

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            summary=f"Upload an attachment for a Publication Version",
            response_model=UploadAttachmentResponse,
            description=None,
            tags=["Publication Versions"],
        )

        return router


class UploadPublicationVersionAttachmentEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "upload_publication_version_attachment"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{version_uuid}" in path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return UploadPublicationVersionAttachmentEndpoint(path=path)
