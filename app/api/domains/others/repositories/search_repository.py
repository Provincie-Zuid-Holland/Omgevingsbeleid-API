from abc import ABCMeta, abstractmethod

from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.domains.others.types import ValidSearchConfig
from app.api.utils.pagination import SimplePagination


class SearchRepository(BaseRepository, metaclass=ABCMeta):
    @abstractmethod
    def search(
        self,
        query: str,
        session: Session,
        object_types: list[str] | None,
        pagination: SimplePagination,
        search_config: ValidSearchConfig,
    ):
        pass
