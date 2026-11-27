import uuid
from abc import ABCMeta, abstractmethod

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.base_repository import BaseRepository
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingenTable


class InputGeoOnderverdelingRepository(BaseRepository, metaclass=ABCMeta):
    @abstractmethod
    def _text_to_shape(self, key: str) -> str:
        pass

    @abstractmethod
    def _format_uuid(self, idx: uuid.UUID) -> str:
        pass

    async def get_by_uuid(self, session: AsyncSession, idx: uuid.UUID) -> InputGeoOnderverdelingenTable | None:
        stmt = select(InputGeoOnderverdelingenTable).filter(InputGeoOnderverdelingenTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_latest_by_title(self, session: AsyncSession, title: str) -> InputGeoOnderverdelingenTable | None:
        stmt = (
            select(InputGeoOnderverdelingenTable)
            .filter(InputGeoOnderverdelingenTable.title == title)
            .order_by(desc(InputGeoOnderverdelingenTable.created_date))
        )
        return await self.fetch_first(session, stmt)
