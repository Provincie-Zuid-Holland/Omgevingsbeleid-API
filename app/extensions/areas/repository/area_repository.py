from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import undefer

from app.dynamic.repository.repository import BaseRepository
from app.extensions.areas.db.tables import AreasTable


class AreaRepository(BaseRepository):
    def get_by_uuid(self, uuidx: UUID) -> Optional[AreasTable]:
        stmt = select(AreasTable).filter(AreasTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_by_werkingsgebied_uuid(self, werkingsgebied_uuid: UUID) -> Optional[AreasTable]:
        stmt = select(AreasTable).filter(AreasTable.Source_UUID == werkingsgebied_uuid)
        return self.fetch_first(stmt)

    def get_with_gml(self, uuidx: UUID) -> Optional[AreasTable]:
        stmt = select(AreasTable).options(undefer(AreasTable.Gml)).filter(AreasTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_many_with_gml(self, uuids: List[UUID]) -> List[AreasTable]:
        if len(uuids) == 0:
            return []

        stmt = select(AreasTable).options(undefer("Gml")).filter(AreasTable.UUID.in_(uuids))
        return self.fetch_all(stmt)
