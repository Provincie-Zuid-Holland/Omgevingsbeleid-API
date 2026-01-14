from typing import Optional
import uuid
from abc import ABCMeta, abstractmethod

from sqlalchemy import select
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

    def get_by_uuid(self, session: Session, uuidx: uuid.UUID) -> Optional[InputGeoOnderverdelingenTable]:
        stmt = select(InputGeoOnderverdelingenTable).filter(InputGeoOnderverdelingenTable.UUID == uuid)
        return self.fetch_first(session, stmt)
