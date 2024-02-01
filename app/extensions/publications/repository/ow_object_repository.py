from typing import List, Optional
from uuid import UUID

from sqlalchemy import select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult
from app.extensions.publications.tables.ow import OWAmbtsgebiedTable, OWObjectTable


class OWObjectRepository(BaseRepository):
    """
    Repository for handling OWObject-related database operations.
    """

    def create_ow_object(self, new_ow_object: OWObjectTable) -> OWObjectTable:
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

    def create_ow_objects(self, new_ow_objects: List[OWObjectTable]) -> List[OWObjectTable]:
        """
        Creates multiple new OWObjects.

        Args:
            new_ow_objects (List[OWObject]): The list of OWObjects to be created.

        Returns:
            List[OWObject]: The list of created OWObjects.
        """
        # TODO: This is a temp fix, make sure ambstgebied is only generated when needed
        for new_ow_object in new_ow_objects:
            if isinstance(new_ow_object, OWAmbtsgebiedTable):
                existing: OWAmbtsgebiedTable = self.get_ow_object_by_uuid(new_ow_object.uuid)
                if existing:
                    existing.OW_ID = new_ow_object.OW_ID
                    existing.Modified_Date = new_ow_object.Modified_Date
                    existing.Bestuurlijke_grenzen_id = new_ow_object.Bestuurlijke_grenzen_id
                    existing.Geldig_Op = new_ow_object.Geldig_Op
                    existing.Domein = new_ow_object.Domein
                    self._db.flush()
                    continue
            self._db.add(new_ow_object)
        self._db.commit()
        return new_ow_objects

    def get_ow_object_by_uuid(self, uuid: UUID) -> Optional[OWObjectTable]:
        """
        Retrieves an OWObject by its UUID.

        Args:
            uuid (UUID): The UUID of the OWObject.

        Returns:
            Optional[OWObject]: The OWObject with the specified UUID, or None if not found.
        """
        stmt = select(OWObjectTable).where(OWObjectTable.UUID == uuid)
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
        query = select(OWObjectTable)
        paged_result = self.fetch_paginated(
            statement=query,
            offset=offset,
            limit=limit,
            sort=(OWObjectTable.Modified_Date, "desc"),
        )
        return paged_result
