import uuid
from abc import ABCMeta, abstractmethod

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingenTable


class InputGeoOnderverdelingRepository(BaseRepository, metaclass=ABCMeta):
    @abstractmethod
    def _text_to_shape(self, key: str) -> str:
        pass

    @abstractmethod
    def _format_uuid(self, idx: uuid.UUID) -> str:
        pass

    def get_by_uuid(self, session: Session, idx: uuid.UUID) -> InputGeoOnderverdelingenTable | None:
        stmt = select(InputGeoOnderverdelingenTable).filter(InputGeoOnderverdelingenTable.id == idx)
        return self.fetch_first(session, stmt)

    def get_latest_by_title(self, session: Session, title: str) -> InputGeoOnderverdelingenTable | None:
        stmt = (
            select(InputGeoOnderverdelingenTable)
            .filter(InputGeoOnderverdelingenTable.title == title)
            .order_by(desc(InputGeoOnderverdelingenTable.created_date))
        )
        return self.fetch_first(session, stmt)
