from typing import Annotated

import click
from dependency_injector.wiring import inject, Provide
from jedi.inference.value.iterable import Sequence

from app.api.api_container import ApiContainer
from app.api.domains.others.repositories import StorageFileRepository
from app.api.domains.others.services import PdfMetaService
from app.api.domains.publications.repository import PublicationStorageFileRepository
from app.core.db.session import SessionFactoryType, session_scope_with_context
from app.core.tables.others import StorageFileTable
from app.core.tables.publications import PublicationStorageFileTable


@click.command()
@inject
def check_pdfs(
    db_session_factory: Annotated[SessionFactoryType, Provide[ApiContainer.db_session_factory]],
    storage_file_repository: Annotated[StorageFileRepository, Provide[ApiContainer.storage_file_repository]],
    publication_storage_file_repository: Annotated[
        PublicationStorageFileRepository, Provide[ApiContainer.publication.storage_file_repository]
    ],
    pdf_meta_service: Annotated[PdfMetaService, Provide[ApiContainer.pdf_meta_service]],
):
    with session_scope_with_context(db_session_factory) as session:
        storage_files: Sequence[StorageFileTable] = storage_file_repository.get_all(session)

        for storage_file in storage_files:
            report_list = pdf_meta_service.report_banned_meta(storage_file.Binary)
            if len(report_list) <= 0:
                continue

            print(f"Storage file {storage_file.UUID} with name {storage_file.Filename} has the following report:")
            for report in report_list:
                print(f"- {report.key} {report.value} {report.type}")

        publication_storage_files: Sequence[PublicationStorageFileTable] = publication_storage_file_repository.get_all(
            session
        )
        for publication_storage_file in publication_storage_files:
            report_list = pdf_meta_service.report_banned_meta(publication_storage_file.Binary)
            if len(report_list) <= 0:
                continue

            print(
                f"Publication storage file {storage_file.UUID} with name {storage_file.Filename} has the following report:"
            )
            for report in report_list:
                print(f"- {report.key} {report.value} {report.type}")
