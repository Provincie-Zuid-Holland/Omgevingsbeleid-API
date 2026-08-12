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
    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        pass

    def get_by_uuid(self, session: Session, uuidx: uuid.UUID) -> InputGeoOnderverdelingenTable | None:
        stmt = select(InputGeoOnderverdelingenTable).filter(InputGeoOnderverdelingenTable.UUID == uuidx)
        return self.fetch_first(session, stmt)

    def get_latest_by_title(self, session: Session, title: str) -> InputGeoOnderverdelingenTable | None:
        stmt = (
            select(InputGeoOnderverdelingenTable)
            .filter(InputGeoOnderverdelingenTable.Title == title)
            .order_by(desc(InputGeoOnderverdelingenTable.Created_Date))
        )
        return self.fetch_first(session, stmt)
