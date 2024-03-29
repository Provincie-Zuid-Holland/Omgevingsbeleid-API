import uuid
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.dynamic.repository.repository import BaseRepository


class GeometryRepository(BaseRepository, metaclass=ABCMeta):
    @abstractmethod
    def add_onderverdeling(
        self,
        uuidx: uuid.UUID,
        idx: int,
        title: str,
        text_shape: str,
        symbol: str,
        werkingsgebied_title: str,
        werkingsgebied_uuid: uuid.UUID,
        created_date: datetime,
        modified_date: datetime,
        start_validity: datetime,
        end_validity: Optional[datetime],
    ):
        pass

    @abstractmethod
    def add_werkingsgebied(
        self,
        uuidx: uuid.UUID,
        idx: int,
        title: str,
        text_shape: str,
        gml: str,
        symbol: str,
        created_date: datetime,
        modified_date: datetime,
        start_validity: datetime,
        end_validity: Optional[datetime],
    ):
        pass

    @abstractmethod
    def get_werkingsgebied(self, uuidx: uuid.UUID) -> dict:
        pass

    @abstractmethod
    def get_werkingsgebied_optional(self, uuidx: uuid.UUID) -> Optional[dict]:
        pass

    @abstractmethod
    def get_onderverdelingen_for_werkingsgebied(self, werkingsgebied_uuid: uuid.UUID) -> List[dict]:
        pass
