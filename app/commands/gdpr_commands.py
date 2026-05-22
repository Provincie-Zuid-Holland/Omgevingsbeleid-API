import base64
import binascii
import io
import logging
import re
from typing import Annotated, Sequence, List, Dict, Optional

import click
from PIL import Image, ExifTags, UnidentifiedImageError
from PIL.Image import Exif
from dependency_injector.wiring import inject, Provide
from sqlalchemy import select, Select

from app.api.api_container import ApiContainer
from app.api.domains.objects.repositories.asset_repository import AssetRepository
from app.api.domains.others.repositories import StorageFileRepository
from app.api.domains.others.services import PdfMetaService
from app.api.domains.others.services.pdf_meta_service import PdfMetaReport
from app.api.domains.publications.repository import PublicationStorageFileRepository
from app.core.db.session import SessionFactoryType, session_scope_with_context
from app.core.tables.others import StorageFileTable, AssetsTable
from app.core.tables.publications import PublicationStorageFileTable

logger = logging.getLogger(__name__)


@click.command()
@inject
def check_pdfs(
    db_session_factory: Annotated[SessionFactoryType, Provide[ApiContainer.db_session_factory]],
    storage_file_repository: Annotated[StorageFileRepository, Provide[ApiContainer.storage_file_repository]],
    publication_storage_file_repository: Annotated[
        PublicationStorageFileRepository, Provide[ApiContainer.publication.storage_file_repository]
    ],
    pdf_meta_service: Annotated[PdfMetaService, Provide[ApiContainer.pdf_meta_service]],
) -> None:
    with session_scope_with_context(db_session_factory) as session:
        stmt: Select = select(StorageFileTable)
        storage_files: Sequence[StorageFileTable] = storage_file_repository.iter_all(session, stmt)

        for storage_file in storage_files:
            report_list: List[PdfMetaReport] = pdf_meta_service.report_banned_meta(storage_file.Binary)
            if len(report_list) <= 0:
                continue

            log_list: List[str] = [
                f"Storage file {storage_file.UUID} with name {storage_file.Filename} has the following report:"
            ]
            for report in report_list:
                log_list.append(f"- {report.key} {report.value} {report.type}")
            logger.info("\n".join(log_list))

        publication_storage_files: Sequence[PublicationStorageFileTable] = publication_storage_file_repository.get_all(
            session
        )
        for publication_storage_file in publication_storage_files:
            report_list: List[PdfMetaReport] = pdf_meta_service.report_banned_meta(publication_storage_file.Binary)
            if len(report_list) <= 0:
                continue

            log_list: List[str] = [
                f"Publication storage file {storage_file.UUID} with name {storage_file.Filename} has the following report:"
            ]
            for report in report_list:
                log_list.append(f"- {report.key} {report.value} {report.type}")
            logger.info("\n".join(log_list))


@click.command()
@inject
def check_images(
    db_session_factory: Annotated[SessionFactoryType, Provide[ApiContainer.db_session_factory]],
    asset_repository: Annotated[AssetRepository, Provide[ApiContainer.asset_repository]],
) -> None:
    with session_scope_with_context(db_session_factory) as session:
        stmt: Select = select(AssetsTable)
        assets: Sequence[AssetsTable] = asset_repository.iter_all(session, stmt)
        for asset in assets:
            match: Optional[re.Match[str]] = re.match(r"data:image/(.*?);base64,(.*)", asset.Content)
            if not match:
                logger.warning(f"Asset {asset.UUID} does not have image data")
                continue

            mime_type, base64_data = match.groups()
            if mime_type not in ["png", "jpg", "jpeg"]:
                logger.warning(f"Asset {asset.UUID} has a unknown type {mime_type}")
                continue

            try:
                picture_data = base64.b64decode(base64_data)
            except binascii.Error as e:
                logger.warning(f"Asset {asset.UUID} has invalid base64: {e}")
                continue

            try:
                with Image.open(io.BytesIO(picture_data)) as image:
                    exif_data: Exif = image.getexif()
                    if not exif_data:
                        continue
                    exif_keys: Dict[str, str] = {
                        ExifTags.TAGS.get(tag_id, tag_id): str(value) for tag_id, value in exif_data.items()
                    }
                    logger.info(f"Asset {asset.UUID} has exif data: {exif_keys}")
            except UnidentifiedImageError as e:
                logger.warning(f"Asset {asset.UUID}'s file can't be opened: {e}")
