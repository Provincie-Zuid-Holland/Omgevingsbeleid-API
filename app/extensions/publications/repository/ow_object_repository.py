from app.core.db.base import Base
from app.extensions.publications.enums import IMOWTYPE, OWProcedureStatus, OWAssociationType
from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SimplePagination
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from .ow import OWObject


class OWObjectRepository(BaseRepository):
    """
    Repository for handling OWObject-related database operations.
    """

    def create_ow_object(self, new_ow_object: OWObject) -> OWObject:
        """
        Creates a new OWObject.

        Args:
            new_ow_object (OWObject): The OWObject to be created.

        Returns:
            OWObject: The created OWObject.
        """
        self._db.add(new_ow_object)
        self._db.flush()
        self._db.commit()
        return new_ow_object

    def get_ow_object(self, uuid: UUID) -> Optional[OWObject]:
        """
        Retrieves an OWObject by its UUID.

        Args:
            uuid (UUID): The UUID of the OWObject.

        Returns:
            Optional[OWObject]: The OWObject with the specified UUID, or None if not found.
        """
        stmt = select(OWObject).where(OWObject.UUID == uuid)
        return self.fetch_first(stmt)

    def get_ow_objects(self, offset: int = 0, limit: int = 20) -> PaginatedQueryResult:
        """
        Retrieves a list of OWObjects.

        Args:
            offset (int): The offset for pagination.
            limit (int): The limit for pagination.

        Returns:
            PaginatedQueryResult: The paginated query result containing the OWObjects.
        """
        query = select(OWObject)
        paged_result = self.fetch_paginated(
            statement=query,
            offset=offset,
            limit=limit,
            sort=(OWObject.Modified_Date, "desc"),
        )
        return paged_result
