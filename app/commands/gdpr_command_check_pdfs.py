import logging
import uuid
from typing import Annotated, Iterable, List, Optional, Sequence

import click
from dependency_injector.wiring import Provide, inject
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.modules import ModuleObjectRepository
from app.api.domains.objects.repositories import ObjectRepository
from app.api.domains.others.repositories import StorageFileRepository
from app.api.domains.others.services import PdfMetaService
from app.api.domains.others.services.pdf_meta_service import PdfMetaReport
from app.api.domains.publications.repository import PublicationStorageFileRepository
from app.commands.gdpr_commands import (
    FilterStrategy,
    KeyStrategy,
    ObjectLookups,
    ObjectTableType,
    Report,
    StorageFileRepositoryType,
    StorageFileTableType,
)
from app.core.db.session import SessionFactoryType, session_scope_with_context
from app.core.tables.others import StorageFileTable
from app.core.tables.publications import PublicationStorageFileTable

logger = logging.getLogger(__name__)


def _file_uuid_filter(storage_file_uuids: List[uuid.UUID]) -> FilterStrategy:
    def _filter(table_type: type[ObjectTableType]):
        return table_type.File_UUID.in_(storage_file_uuids)

    return _filter


def _file_uuid_key() -> KeyStrategy:
    def _key(obj: ObjectTableType) -> Iterable[uuid.UUID]:
        value = getattr(obj, "File_UUID", None)
        return [value] if value else []

    return _key


def _handle_storage_files(
    session: Session,
    table_type: type[StorageFileTableType],
    repository: StorageFileRepositoryType,
    pdf_meta_service: PdfMetaService,
    object_repository: ObjectRepository,
    module_object_repository: ModuleObjectRepository,
    label: str,
) -> None:
    report: Report = {}
    stmt: Select = select(table_type)
    storage_files: Sequence[StorageFileTableType] = repository.iter_all(session, stmt)
    for storage_file in storage_files:
        meta_report_list: List[PdfMetaReport] = pdf_meta_service.report_banned_meta(storage_file.Binary)
        if len(meta_report_list) <= 0:
            continue
        report[storage_file] = [
            f"- {meta_report.key} {meta_report.value} {meta_report.type}" for meta_report in meta_report_list
        ]

    if not report:
        return

    storage_file_uuids: List[uuid.UUID] = [storage_file.UUID for storage_file in report.keys()]
    object_lookups: ObjectLookups = ObjectLookups(
        session,
        object_repository,
        module_object_repository,
    )
    object_lookups.create_all(
        _file_uuid_filter(storage_file_uuids),
        _file_uuid_key(),
    )

    for storage_file, meta_issues in report.items():
        log_list: List[str] = []
        object_log: Optional[str] = object_lookups.get_log(storage_file.UUID) or ""
        log_list.append(
            f"{label} {storage_file.UUID} with name {storage_file.Filename}{object_log} has the following report:"
        )
        for issue in meta_issues:
            log_list.append(issue)
        logger.info("\n".join(log_list))


@click.command()
@inject
def check_pdfs(
    db_session_factory: Annotated[SessionFactoryType, Provide[ApiContainer.db_session_factory]],
    storage_file_repository: Annotated[StorageFileRepository, Provide[ApiContainer.storage_file_repository]],
    publication_storage_file_repository: Annotated[
        PublicationStorageFileRepository, Provide[ApiContainer.publication.storage_file_repository]
    ],
    object_repository: Annotated[ObjectRepository, Provide[ApiContainer.object_repository]],
    module_object_repository: Annotated[ModuleObjectRepository, Provide[ApiContainer.module_object_repository]],
    pdf_meta_service: Annotated[PdfMetaService, Provide[ApiContainer.pdf_meta_service]],
) -> None:
    with session_scope_with_context(db_session_factory) as session:
        _handle_storage_files(
            session,
            StorageFileTable,
            storage_file_repository,
            pdf_meta_service,
            object_repository,
            module_object_repository,
            "Storage file",
        )
        _handle_storage_files(
            session,
            PublicationStorageFileTable,
            publication_storage_file_repository,
            pdf_meta_service,
            object_repository,
            module_object_repository,
            "Publication storage file",
        )
