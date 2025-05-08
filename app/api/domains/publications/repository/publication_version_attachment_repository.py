from typing import List, Optional
from uuid import UUID

from sqlalchemy import select

from app.api.base_repository import BaseRepository
from app.core.tables.publications import PublicationVersionAttachmentTable


class PublicationVersionAttachmentRepository(BaseRepository):
    def get_by_id(self, idx: int) -> Optional[PublicationVersionAttachmentTable]:
        stmt = select(PublicationVersionAttachmentTable).filter(PublicationVersionAttachmentTable.ID == idx)
        return self.fetch_first(stmt)

    def get_by_version_uuid(self, version_uuid: UUID) -> List[PublicationVersionAttachmentTable]:
        stmt = select(PublicationVersionAttachmentTable).filter(
            PublicationVersionAttachmentTable.Publication_Version_UUID == version_uuid
        )
        return self.fetch_all(stmt)
