import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.api.domains.others.repositories.storage_file_repository import StorageFileRepository
from app.api.domains.others.services import PdfMetaService
from app.api.domains.others.types import FileData, ObjectRelatedFileResponse
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.others import ObjectRelatedFileTable, StorageFileTable
from app.core.tables.users import UsersTable


class EndpointHandler:
    def __init__(
        self,
        session: Session,
        object_static: ObjectStaticsTable,
        storage_repository: StorageFileRepository,
        pdf_meta_service: PdfMetaService,
        user: UsersTable,
        uploaded_file: UploadFile,
        title: str,
        ignore_report: bool,
    ):
        self._session: Session = session
        self._object_static: ObjectStaticsTable = object_static
        self._storage_repository: StorageFileRepository = storage_repository
        self._pdf_meta_service: PdfMetaService = pdf_meta_service
        self._user: UsersTable = user
        self._uploaded_file: UploadFile = uploaded_file
        self._file_data: FileData = FileData(File=uploaded_file)
        self._title: str = title
        self._ignore_report: bool = ignore_report
        self._timepoint: datetime = datetime.now(timezone.utc)

    def handle(self) -> ObjectRelatedFileResponse:
        self._guard_upload()

        if not self._ignore_report:
            pdf_meta_report = self._pdf_meta_service.report_banned_meta(self._file_data.get_binary())
            if len(pdf_meta_report) > 0:
                raise HTTPException(434, detail=jsonable_encoder(pdf_meta_report))

        file_table: StorageFileTable = self._store_file()

        related_file = ObjectRelatedFileTable(
            UUID=uuid.uuid4(),
            Object_Code=self._object_static.Code,
            File_UUID=file_table.UUID,
            Title=self._title,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        self._session.add(related_file)
        self._session.commit()
        self._session.flush()

        return ObjectRelatedFileResponse.model_validate(related_file)

    def _guard_upload(self):
        if self._uploaded_file.file is None or self._uploaded_file.filename is None:
            raise HTTPException(status_code=400, detail="No file uploaded.")

        if self._uploaded_file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Unsupported file type, expected a PDF.")

    def _store_file(self) -> StorageFileTable:
        existing_file_table: Optional[StorageFileTable] = self._storage_repository.get_by_checksum_uuid(
            self._session,
            self._file_data.get_checksum(),
        )
        if existing_file_table is not None:
            return existing_file_table

        file_table = StorageFileTable(
            UUID=uuid.uuid4(),
            Lookup=self._file_data.get_lookup(),
            Checksum=self._file_data.get_checksum(),
            Filename=self._file_data.normalize_filename(),
            Content_Type=self._file_data.get_content_type(),
            Size=self._file_data.get_size(),
            Binary=self._file_data.get_binary(),
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        self._session.add(file_table)
        self._session.flush()
        return file_table


@inject
def post_object_related_files_upload_endpoint(
    object_type: str,
    lineage_id: int,
    user: Annotated[UsersTable, Depends(depends_current_user)],
    storage_repository: Annotated[StorageFileRepository, Depends(Provide[ApiContainer.storage_file_repository])],
    object_static_repository: Annotated[
        ObjectStaticRepository, Depends(Provide[ApiContainer.object_static_repository])
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    pdf_meta_service: Annotated[PdfMetaService, Depends(Provide[ApiContainer.pdf_meta_service])],
    title: str = Form(...),
    ignore_report: bool = Form(...),
    uploaded_file: UploadFile = File(...),
) -> ObjectRelatedFileResponse:
    object_static: Optional[ObjectStaticsTable] = object_static_repository.get_by_object_type_and_id(
        session, object_type, lineage_id
    )
    if not object_static:
        raise HTTPException(status_code=404, detail="Object niet gevonden")

    permission_service.guard_valid_user(
        Permissions.can_create_object_related_file,
        user,
        [
            object_static.Owner_1_UUID,
            object_static.Owner_2_UUID,
        ],
    )

    handler: EndpointHandler = EndpointHandler(
        session,
        object_static,
        storage_repository,
        pdf_meta_service,
        user,
        uploaded_file,
        title,
        ignore_report,
    )
    return handler.handle()
