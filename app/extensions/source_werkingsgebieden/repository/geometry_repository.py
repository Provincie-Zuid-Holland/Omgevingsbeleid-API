import uuid
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import SimplePagination


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

    @abstractmethod
    def get_werkingsgebieden_hashed(self, pagination: SimplePagination, title: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def get_werkingsgebieden_grouped_by_title(self, pagination: SimplePagination) -> Tuple[int, List[Dict[str, Any]]]:
        pass
