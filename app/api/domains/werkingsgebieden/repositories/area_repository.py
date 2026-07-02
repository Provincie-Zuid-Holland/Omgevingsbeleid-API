from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, undefer

from app.api.base_repository import BaseRepository
from app.core.tables.others import AreasTable


class AreaRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuidx: UUID) -> Optional[AreasTable]:
        stmt = select(AreasTable).filter(AreasTable.UUID == uuidx)
        return self.fetch_first(session, stmt)

    def get_by_source_uuid(self, session: Session, werkingsgebied_uuid: UUID) -> Optional[AreasTable]:
        stmt = select(AreasTable).filter(AreasTable.Source_UUID == werkingsgebied_uuid)
        return self.fetch_first(session, stmt)

    def get_by_source_hash_and_title(
        self, session: Session, source_hash: str, source_title: str
    ) -> Optional[AreasTable]:
        if not source_hash:
            return None

        lookup: str = source_hash[0:10]
        stmt = (
            select(AreasTable)
            .filter(AreasTable.Source_Geometry_Index == lookup)
            .filter(AreasTable.Source_Geometry_Hash == source_hash)
            .filter(AreasTable.Source_Title == source_title)
        )
        return self.fetch_first(session, stmt)

    def get_by_source_hash(self, session: Session, source_hash: str) -> Optional[AreasTable]:
        if not source_hash:
            return None

        lookup: str = source_hash[0:10]
        stmt = (
            select(AreasTable)
            .filter(AreasTable.Source_Geometry_Index == lookup)
            .filter(AreasTable.Source_Geometry_Hash == source_hash)
        )
        return self.fetch_first(session, stmt)

    def get_with_gml(self, session: Session, uuidx: UUID) -> Optional[AreasTable]:
        stmt = select(AreasTable).options(undefer(AreasTable.Gml)).filter(AreasTable.UUID == uuidx)
        return self.fetch_first(session, stmt)

    def get_many_with_gml(self, session: Session, uuids: List[UUID]) -> List[AreasTable]:
        if len(uuids) == 0:
            return []

        stmt = select(AreasTable).options(undefer("Gml")).filter(AreasTable.UUID.in_(uuids))
        return self.fetch_all(session, stmt)
