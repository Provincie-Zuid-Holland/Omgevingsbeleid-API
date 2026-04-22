import base64
import io
import re
from typing import Annotated, Sequence

import click
from PIL import Image, ExifTags, UnidentifiedImageError
from dependency_injector.wiring import inject, Provide

from app.api.api_container import ApiContainer
from app.api.domains.others.repositories import StorageFileRepository
from app.api.domains.others.services import PdfMetaService
from app.api.domains.publications.repository import PublicationStorageFileRepository
from app.core.db.session import SessionFactoryType, session_scope_with_context
from app.core.tables.others import StorageFileTable, AssetsTable
from app.core.tables.publications import PublicationStorageFileTable
from app.api.domains.objects.repositories.asset_repository import AssetRepository


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


@click.command()
@inject
def check_images(
    db_session_factory: Annotated[SessionFactoryType, Provide[ApiContainer.db_session_factory]],
    asset_repository: Annotated[AssetRepository, Provide[ApiContainer.asset_repository]],
):
    with session_scope_with_context(db_session_factory) as session:
        assets: Sequence[AssetsTable] = asset_repository.get_all(session)
        for asset in assets:
            match = re.match(r"data:image/(.*?);base64,(.*)", asset.Content)
            if not match:
                print(f"Asset {asset.UUID} does not have image data")

            mime_type, base64_data = match.groups()
            if mime_type not in ["png", "jpg", "jpeg"]:
                print(f"Asset {asset.UUID} has a unknown type {mime_type}")

            picture_data = base64.b64decode(base64_data)
            try:
                image = Image.open(io.BytesIO(picture_data))
                exif_data = image.getexif()
                if exif_data:
                    exif_keys = {ExifTags.TAGS.get(tag_id, tag_id): value for tag_id, value in exif_data.items()}
                    print(f"Asset {asset.UUID} has exif data: {exif_keys}")
            except UnidentifiedImageError as e:
                print(f"Error opening asset {asset.UUID}: {e}")
