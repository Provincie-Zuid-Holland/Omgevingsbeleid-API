from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.tables.tables import PublicationTable


class PublicationRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[PublicationTable]:
        stmt = select(PublicationTable).where(PublicationTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        document_type: Optional[DocumentType] = None,
        module_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if document_type is not None:
            filters.append(and_(PublicationTable.Document_Type == document_type))
        if module_id is not None:
            filters.append(and_(PublicationTable.Module_ID == module_id))

        stmt = select(PublicationTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result

    # @todo: move all of these
    # def create_publication_package(self, new_package: PublicationPackageTable) -> PublicationPackageTable:
    #     """
    #     Creates a publication package and automatically sets the FRBR if it's a validation package.

    #     Args:
    #         new_package (PublicationPackageTable): The new publication package to be created.

    #     Returns:
    #         PublicationPackageTable: The created publication package.
    #     """
    #     frbr = None
    #     # If validation package, create new FRBR
    #     if new_package.Package_Event_Type == PackageType.VALIDATION:
    #         bill = self.get_publication_bill(new_package.Bill_UUID)
    #         frbr = PublicationFRBRTable.create_default_frbr(
    #             document_type=bill.Publication.Document_Type,
    #             expression_version=bill.Version_ID,
    #             work_ID=bill.Publication.Work_ID,
    #         )
    #         new_package.FRBR_Info = frbr
    #     else:
    #         # if publication event, try using earlier FRBR created at validation version of this bill
    #         stmt = (
    #             select(PublicationPackageTable)
    #             .where(
    #                 PublicationPackageTable.Bill_UUID == new_package.Bill_UUID,
    #                 PublicationPackageTable.Package_Event_Type == PackageType.VALIDATION,
    #                 PublicationPackageTable.Validation_Status == ValidationStatusType.VALID,
    #             )
    #             .order_by(desc(PublicationPackageTable.Modified_Date))
    #             .limit(1)
    #         )
    #         validated_package = self.fetch_first(stmt)
    #         if not validated_package:
    #             raise ValueError("No validated package found for this bill")
    #         new_package.FRBR_ID = validated_package.FRBR_ID

    #     self._db.add(new_package)
    #     self._db.flush()
    #     self._db.commit()
    #     return new_package

    # def get_publication_package(self, uuid: UUID) -> Optional[PublicationPackageTable]:
    #     """
    #     Retrieves full publication package by its UUID.
    #     """
    #     stmt = (
    #         select(PublicationPackageTable)
    #         .where(PublicationPackageTable.UUID == uuid)
    #         .options(selectinload(PublicationPackageTable.Reports))
    #     )
    #     return self.fetch_first(stmt)

    # def get_publication_packages(
    #     self,
    #     bill_uuid: Optional[UUID] = None,
    #     package_event_type: Optional[PackageType] = None,
    #     is_successful: Optional[bool] = None,
    #     offset: int = 0,
    #     limit: int = 20,
    # ) -> PaginatedQueryResult:
    #     """
    #     Retrieves publication packages based on the provided filters.

    #     Args:
    #         bill_uuid (Optional[UUID]): The UUID of the bill to filter by.
    #         package_event_type (Optional[Package_Event_Type]): The event type of the package to filter by.
    #         is_successful (Optional[bool]): Whether the package is successful or not.
    #         offset (int): The offset value for pagination.
    #         limit (int): The limit value for pagination.

    #     Returns:
    #         PaginatedQueryResult: The paginated query result containing the publication packages.
    #     """
    #     query = select(PublicationPackageTable).options(selectinload(PublicationPackageTable.Reports))
    #     if bill_uuid is not None:
    #         query = query.filter(PublicationPackageTable.Bill_UUID == bill_uuid)
    #     if package_event_type is not None:
    #         query = query.filter(PublicationPackageTable.Package_Event_Type == package_event_type)
    #     if is_successful is not None:
    #         if is_successful:
    #             query = query.filter(PublicationPackageTable.Validation_Status == ValidationStatusType.VALID)
    #         else:
    #             query = query.filter(
    #                 PublicationPackageTable.Validation_Status.in_(
    #                     [ValidationStatusType.FAILED.value, ValidationStatusType.PENDING.value]
    #                 )
    #             )

    #     paged_result = self.fetch_paginated(
    #         statement=query,
    #         offset=offset,
    #         limit=limit,
    #         sort=(PublicationPackageTable.Modified_Date, "desc"),
    #     )
    #     return paged_result

    # def get_package_download(self, package_uuid: UUID) -> Optional[PublicationPackageTable]:
    #     stmt = select(PublicationPackageTable).where(PublicationPackageTable.UUID == package_uuid)
    #     stmt = stmt.options(defer(PublicationPackageTable.ZIP_File_Binary))
    #     return self.fetch_first(stmt)

    # def get_frbr_by_id(self, frbr_id: int) -> Optional[PublicationFRBRTable]:
    #     stmt = select(PublicationFRBRTable).where(PublicationFRBRTable.ID == frbr_id)
    #     return self.fetch_first(stmt)

    # def create_default_frbr(
    #     self,
    #     document_type: str,
    #     work_ID: int,
    #     expression_version: int,
    # ) -> PublicationFRBRTable:
    #     """
    #     Creates a default FRBR (Functional Requirements for Bibliographic Records) entry
    #     for a publication.

    #     Args:
    #         document_type (str): The type of the document.
    #         work_ID (int): The ID of the work.
    #         expression_version (int): The version of the expression.

    #     Returns:
    #         PublicationFRBRTable: The newly created FRBR entry.
    #     """
    #     timepoint: datetime = datetime.utcnow()
    #     current_year = timepoint.year
    #     current_date = timepoint.strftime("%Y-%m-%d")

    #     new_frbr = PublicationFRBRTable(
    #         Created_Date=timepoint,
    #         # Fields for bill_frbr
    #         bill_work_country="nl",
    #         bill_work_date=str(current_year),
    #         bill_work_misc=f"{document_type}_{work_ID}",
    #         bill_expression_lang="nld",
    #         bill_expression_date=current_date,
    #         bill_expression_version=str(expression_version),
    #         bill_expression_misc=None,
    #         # Fields for act_frbr
    #         act_work_country="nl",
    #         act_work_date=str(current_year),
    #         act_work_misc=f"{document_type}_{work_ID}",
    #         act_expression_lang="nld",
    #         act_expression_date=current_date,
    #         act_expression_version=str(expression_version),
    #         act_expression_misc=None,
    #     )

    #     self._db.add(new_frbr)
    #     self._db.flush()
    #     self._db.commit()
    #     return new_frbr
