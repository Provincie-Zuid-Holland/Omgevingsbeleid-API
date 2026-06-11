import base64
import binascii
import io
import logging
import re
import uuid
from typing import Annotated, Any, Dict, Iterable, List, Optional, Sequence, Set

import click
from PIL import ExifTags, Image, UnidentifiedImageError
from PIL.Image import Exif
from dependency_injector.wiring import Provide, inject
from sqlalchemy import BinaryExpression, Column, Select, or_, select

from app.api.api_container import ApiContainer
from app.api.domains.modules import ModuleObjectRepository
from app.api.domains.objects.repositories import AssetRepository, ObjectRepository
from app.commands.gdpr_commands import FilterStrategy, KeyStrategy, ObjectLookups, ObjectTableType, Report
from app.core.db.session import SessionFactoryType, session_scope_with_context
from app.core.tables.others import AssetsTable

logger = logging.getLogger(__name__)

ASSET_PATTERN = re.compile(r"\[ASSET:([0-9a-fA-F-]{36})]")


def _format_exif_value(value: Any, max_length: int = 50) -> str:
    if isinstance(value, bytes):
        value_str: str = value.decode(errors="ignore")
    else:
        value_str: str = str(value)

    if len(value_str) > max_length:
        return value_str[:max_length] + "..."
    return value_str


def _asset_key() -> KeyStrategy:
    def _key(object_in: ObjectTableType) -> Iterable[uuid.UUID]:
        uuids: Set[uuid.UUID] = set()
        for column in [
            object_in.Description,
            object_in.Cause,
            object_in.Effect,
            object_in.Explanation,
            object_in.Provincial_Interest,
        ]:
            if not column:
                continue

            for match in ASSET_PATTERN.findall(column):
                uuids.add(uuid.UUID(match))
        return uuids

    return _key


def _asset_filter(asset_uuids: Set[uuid.UUID]) -> FilterStrategy:
    def _filter(table_type: type[ObjectTableType]):
        columns: List[Column] = [
            table_type.Cause,
            table_type.Description,
            table_type.Effect,
            table_type.Explanation,
            table_type.Provincial_Interest,
        ]
        conditions: List[BinaryExpression[bool]] = [
            column.like(f"%ASSET:{asset_uuid}%") for column in columns for asset_uuid in asset_uuids
        ]
        return or_(*conditions)

    return _filter


@click.command()
@inject
def check_images(
    db_session_factory: Annotated[SessionFactoryType, Provide[ApiContainer.db_session_factory]],
    object_repository: Annotated[ObjectRepository, Provide[ApiContainer.object_repository]],
    module_object_repository: Annotated[ModuleObjectRepository, Provide[ApiContainer.module_object_repository]],
    asset_repository: Annotated[AssetRepository, Provide[ApiContainer.asset_repository]],
) -> None:
    report: Report = {}
    with session_scope_with_context(db_session_factory) as session:
        stmt: Select = select(AssetsTable)
        assets: Sequence[AssetsTable] = asset_repository.iter_all(session, stmt)
        for asset in assets:
            match: Optional[re.Match[str]] = re.match(r"data:image/(.*?);base64,(.*)", asset.Content)
            if not match:
                report[asset] = ["No image data"]
                continue

            mime_type, base64_data = match.groups()
            if mime_type not in ["png", "jpg", "jpeg"]:
                report[asset] = [f"Unknown type {mime_type}"]
                continue

            try:
                picture_data = base64.b64decode(base64_data)
            except binascii.Error as e:
                report[asset] = [f"Invalid base64: {e}"]
                continue

            try:
                with Image.open(io.BytesIO(picture_data)) as image:
                    exif_data: Exif = image.getexif()
                    if not exif_data:
                        continue
                    exif_keys: Dict[str, str] = {
                        ExifTags.TAGS.get(tag_id, tag_id): _format_exif_value(value)
                        for tag_id, value in exif_data.items()
                    }
                    report[asset] = [f"Has exif data: {exif_keys}"]
            except UnidentifiedImageError:
                report[asset] = ["File can't be opened: {e}"]

        if not report:
            return

        asset_uuids: Set[uuid.UUID] = {asset.UUID for asset in report.keys()}
        object_lookups: ObjectLookups = ObjectLookups(
            session,
            object_repository,
            module_object_repository,
        )
        object_lookups.create_all(
            _asset_filter(asset_uuids),
            _asset_key(),
        )

        for asset, issues in report.items():
            message: str = "\n".join(issues)
            object_log: Optional[str] = object_lookups.get_log(asset.UUID) or ""
            logger.info(f"Asset {asset.UUID}{object_log} has the following message: {message}")
