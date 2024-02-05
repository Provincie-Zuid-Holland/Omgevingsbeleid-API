from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import desc, func, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult
from app.extensions.modules.db.tables import ModuleStatusHistoryTable
from app.extensions.modules.models.models import ModuleStatusCode
from app.extensions.publications import (
    Document_Type,
    PublicationBillTable,
    PublicationConfigTable,
    PublicationPackageTable,
)
from app.extensions.publications.enums import Package_Event_Type
from app.extensions.publications.exceptions import PublicationBillNotFound, PublicationNotFound
from app.extensions.publications.tables.tables import DSOStateExportTable, PublicationFRBRTable, PublicationTable


class PublicationRepository(BaseRepository):
    """
    Repository for handling publication-related database operations.
    """

    def create_publication(self, new_publication: PublicationTable) -> PublicationTable:
        """
        Creates a new publication in the database and automatically sets the Work_ID.

        Args:
            new_publication (PublicationTable): The publication to be created.

        Returns:
            PublicationTable: The created publication.
        """

        max_id = (
            self._db.query(func.max(PublicationTable.Work_ID))
            .filter_by(Document_Type=new_publication.Document_Type)
            .scalar()
        )
        next_id = 1 if max_id is None else max_id + 1
        new_publication.Work_ID = next_id

        self._db.add(new_publication)
        self._db.flush()
        self._db.commit()
        return new_publication

    def get_publication_by_uuid(self, uuid: UUID) -> Optional[PublicationTable]:
        """
        Retrieves a publication by its UUID.

        Args:
            uuid (UUID): The UUID of the publication.

        Returns:
            Optional[PublicationTable]: The publication with the specified UUID, or None if not found.
        """
        stmt = select(PublicationTable).where(PublicationTable.UUID == uuid)
        return self.fetch_first(stmt)

    def list_publications(
        self,
        document_type: Optional[Document_Type] = None,
        module_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        """
        Retrieves a list of publications based on the specified filters.

        Args:
            document_type (Optional[Document_Type]): The document type to filter by.
            module_id (Optional[int]): The module ID to filter by.
            offset (int): The offset for pagination.
            limit (int): The limit for pagination.

        Returns:
            PaginatedQueryResult: The paginated query result containing the publications.
        """
        query = select(PublicationTable)
        if document_type is not None:
            query = query.filter(PublicationTable.Document_Type == document_type)
        if module_id is not None:
            query = query.filter(PublicationTable.Module_ID == module_id)

        paged_result = self.fetch_paginated(
            statement=query,
            offset=offset,
            limit=limit,
            sort=(PublicationTable.Modified_Date, "desc"),
        )
        return paged_result

    def update_publication(self, publication_uuid: UUID, **kwargs) -> PublicationTable:
        """
        Updates a publication with the specified values.

        Args:
            publication_uuid (UUID): The UUID of the publication to be updated.
            **kwargs: The values to be updated.

        Returns:
            PublicationTable: The updated publication.
        """
        publication = self.get_publication_by_uuid(publication_uuid)
        if publication is None:
            raise PublicationNotFound(f"Publication with UUID {publication_uuid} not found.")

        publication.Modified_Date = datetime.now()
        for key, value in kwargs.items():
            setattr(publication, key, value)
        self._db.flush()
        self._db.commit()
        return publication

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
        publication_uuid: Optional[UUID] = None,
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
        if publication_uuid is not None:
            query = query.filter(PublicationBillTable.Publication_UUID == publication_uuid)
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
        max_id = (
            self._db.query(func.max(PublicationBillTable.Version_ID))
            .filter_by(Publication_UUID=new_bill.Publication_UUID)
            .scalar()
        )
        next_id = 1 if max_id is None else max_id + 1
        new_bill.Version_ID = next_id
        self._db.add(new_bill)
        self._db.flush()
        self._db.commit()
        return new_bill

    def update_publication_bill(self, bill_uuid: UUID, **kwargs) -> PublicationBillTable:
        """
        Updates a publication bill with the specified values.

        Args:
            **kwargs: The values to be updated.

        Returns:
            PublicationBillTable: The updated publication bill.
        """
        bill = self.get_publication_bill(bill_uuid)
        if bill is None:
            raise PublicationBillNotFound(f"Publication bill with UUID {bill_uuid} not found.")

        bill.Modified_Date = datetime.now()
        for key, value in kwargs.items():
            setattr(bill, key, value)

        self._db.flush()
        self._db.commit()
        return bill

    def create_publication_package(self, new_package: PublicationPackageTable) -> PublicationPackageTable:
        frbr = None
        # If validation package, create new FRBR
        if new_package.Package_Event_Type == Package_Event_Type.VALIDATION:
            bill = self.get_publication_bill(new_package.Bill_UUID)
            frbr = PublicationFRBRTable.create_default_frbr(
                document_type=bill.Publication.Document_Type,
                expression_version=bill.Version_ID,
                work_ID=bill.Publication.Work_ID,
            )
            new_package.FRBR_Info = frbr
        else:
            # if publication event, use earlier FRBR created at validation version of this bill
            stmt = (
                select(PublicationPackageTable)
                .where(
                    PublicationPackageTable.Bill_UUID == new_package.Bill_UUID,
                    PublicationPackageTable.Package_Event_Type == Package_Event_Type.VALIDATION,
                    PublicationPackageTable.Validated_At.isnot(None),
                )
                .order_by(desc(PublicationPackageTable.Modified_Date))
                .limit(1)
            )
            validated_package = self.fetch_first(stmt)
            new_package.FRBR_ID = validated_package.FRBR_ID

        self._db.add(new_package)
        self._db.flush()
        self._db.commit()
        return new_package

    def get_publication_package(self, uuid: UUID) -> Optional[PublicationPackageTable]:
        """
        Retrieves full publication package by its UUID.
        # TODO add zip uuid
        """
        stmt = select(PublicationPackageTable).where(PublicationPackageTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_publication_packages(
        self,
        bill_uuid: Optional[UUID] = None,
        package_event_type: Optional[Package_Event_Type] = None,
        is_validated: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        query = select(PublicationPackageTable)
        if bill_uuid is not None:
            query = query.filter(PublicationPackageTable.Bill_UUID == bill_uuid)
        if package_event_type is not None:
            query = query.filter(PublicationPackageTable.Package_Event_Type == package_event_type)
        if is_validated is not None:
            query = query.filter(PublicationPackageTable.Validated_At.isnot(None))

        paged_result = self.fetch_paginated(
            statement=query,
            offset=offset,
            limit=limit,
            sort=(PublicationPackageTable.Modified_Date, "desc"),
        )
        return paged_result

    def get_package_download(self, package_uuid: UUID) -> Optional[PublicationPackageTable]:
        stmt = select(PublicationPackageTable).where(PublicationPackageTable.UUID == package_uuid)
        stmt = stmt.options(defer(PublicationPackageTable.ZIP_File_Binary))
        return self.fetch_first(stmt)

    def get_frbr_by_id(self, frbr_id: int) -> Optional[PublicationFRBRTable]:
        stmt = select(PublicationFRBRTable).where(PublicationFRBRTable.ID == frbr_id)
        return self.fetch_first(stmt)

    def create_default_frbr(
        self,
        document_type: str,
        work_ID: int,
        expression_version: int,
    ) -> PublicationFRBRTable:
        """
        Creates a default FRBR (Functional Requirements for Bibliographic Records) entry
        for a publication.

        Args:
            document_type (str): The type of the document.
            work_ID (int): The ID of the work.
            expression_version (int): The version of the expression.

        Returns:
            PublicationFRBRTable: The newly created FRBR entry.
        """
        current_year = datetime.now().year
        current_date = datetime.now().strftime("%Y-%m-%d")

        new_frbr = PublicationFRBRTable(
            Created_Date=datetime.now(),
            # Fields for bill_frbr
            bill_work_country="nl",
            bill_work_date=str(current_year),
            bill_work_misc=f"{document_type}_{work_ID}",
            bill_expression_lang="nld",
            bill_expression_date=current_date,
            bill_expression_version=str(expression_version),
            bill_expression_misc=None,
            # Fields for act_frbr
            act_work_country="nl",
            act_work_date=str(current_year),
            act_work_misc=f"{document_type}_{work_ID}",
            act_expression_lang="nld",
            act_expression_date=current_date,
            act_expression_version=str(expression_version),
            act_expression_misc=None,
        )

        self._db.add(new_frbr)
        self._db.flush()
        self._db.commit()
        return new_frbr

    def get_latest_config(self) -> Optional[PublicationConfigTable]:
        """
        Fetches the latest publication configuration from the database.

        Returns:
            Optional[PublicationConfigTable]: The latest publication configuration, or None if no configuration is found.
        """
        config_query = select(PublicationConfigTable).order_by(desc(PublicationConfigTable.Created_Date)).limit(1)
        return self.fetch_first(config_query)

    def get_config_by_id(self, config_id: int) -> Optional[PublicationConfigTable]:
        config_query = select(PublicationConfigTable).where(PublicationConfigTable.ID == config_id)
        return self.fetch_first(config_query)

    def create_dso_state_export(self, export: DSOStateExportTable) -> DSOStateExportTable:
        self._db.add(export)
        self._db.flush()
        self._db.commit()
        return export
