from datetime import datetime
import json
from typing import Optional
from uuid import UUID, uuid4
import uuid

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.sql import and_, func, or_

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SimplePagination
from app.extensions.modules.db.tables import ModuleStatusHistoryTable
from app.extensions.modules.models.models import ModuleStatusCode
from app.extensions.publications import (
    PublicationBillTable,
    Document_Type,
    PublicationPackageTable,
    PublicationConfigTable,
)


class PublicationRepository(BaseRepository):
    """
    Repository for handling publication-related database operations.
    """

    def get_publication_bill(self, uuid: UUID) -> Optional[PublicationBillTable]:
        """
        Retrieves a publication bill by its UUID.

        Args:
            uuid (UUID): The UUID of the publication bill.

        Returns:
            Optional[PublicationBillTable]: The publication bill with the specified UUID, or None if not found.
        """
        stmt = select(PublicationBillTable).where(PublicationBillTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_publication_bills(
        self,
        document_type: Optional[Document_Type] = None,
        module_id: Optional[int] = None,
        version_id: Optional[int] = None,
        module_status: Optional[ModuleStatusCode] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        """
        Retrieves a list of publication bills based on the specified filters.

        Args:
            document_type (Optional[Document_Type]): The document type to filter by.
            module_id (Optional[int]): The module ID to filter by.
            version_id (Optional[int]): The version ID to filter by.
            module_status (Optional[ModuleStatusCode]): The module status to filter by.
            offset (int): The offset for pagination.
            limit (int): The limit for pagination.

        Returns:
            PaginatedQueryResult: The paginated query result containing the publication bills.
        """
        query = select(PublicationBillTable).join(PublicationBillTable.Module_Status)
        if document_type is not None:
            query = query.filter(PublicationBillTable.Document_Type == document_type)
        if module_id is not None:
            query = query.filter(PublicationBillTable.Module_ID == module_id)
        if version_id is not None:
            query = query.filter(PublicationBillTable.Version_ID == version_id)
        if module_status is not None:
            query = query.filter(ModuleStatusHistoryTable.Status == module_status.value)

        paged_result = self.fetch_paginated(
            statement=query,
            offset=offset,
            limit=limit,
            sort=(PublicationBillTable.Modified_Date, "desc"),
        )
        return paged_result

    def create_publication_bill(self, new_bill: PublicationBillTable) -> PublicationBillTable:
        """
        Creates a new publication bill. Calculates the Version_ID and manually sets it.

        Args:
            new_bill (PublicationBillTable): The publication bill to be created.

        Returns:
            PublicationBillTable: The created publication bill.
        """
        # set version to last known + 1
        new_bill.Version_ID = PublicationBillTable.next_version(
            self._db, new_bill.Module_ID, new_bill.Document_Type
        )
        self._db.add(new_bill)
        self._db.flush()
        self._db.commit()
        return new_bill

    def create_publication_package(
        self, new_package: PublicationPackageTable
    ) -> PublicationPackageTable:
        """
        Creates a new publication package in the database.

        Args:
            new_package (PublicationPackageTable): The new publication package to be created.

        Returns:
            PublicationPackageTable: The newly created publication package.
        """
        self._db.add(new_package)
        self._db.flush()
        self._db.commit()
        return new_package

    def get_publication_packages(
        self,
        document_type: Optional[Document_Type] = None,
        module_id: Optional[int] = None,
        version_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        query = select(PublicationPackageTable).join(PublicationPackageTable.Module_Status)
        if document_type is not None:
            query = query.filter(PublicationPackageTable.Document_Type == document_type)
        if module_id is not None:
            query = query.filter(PublicationPackageTable.Module_ID == module_id)
        if version_id is not None:
            query = query.filter(PublicationPackageTable.Version_ID == version_id)

        paged_result = self.fetch_paginated(
            statement=query,
            offset=offset,
            limit=limit,
            sort=(PublicationPackageTable.Modified_Date, "desc"),
        )
        return paged_result

    def fetch_latest_config(self) -> Optional[PublicationConfigTable]:
        """
        Fetches the latest publication configuration from the database.

        Returns:
            Optional[PublicationConfigTable]: The latest publication configuration, or None if no configuration is found.
        """
        config_query = (
            select(PublicationConfigTable)
            .order_by(desc(PublicationConfigTable.Created_Date))
            .limit(1)
        )
        return self.fetch_first(config_query)
