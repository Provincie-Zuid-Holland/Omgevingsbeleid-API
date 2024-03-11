from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.tables.tables import PublicationPackageTable


class PublicationPackageRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[PublicationPackageTable]:
        stmt = select(PublicationPackageTable).filter(PublicationPackageTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        version_uuid: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if version_uuid is not None:
            filters.append(and_(PublicationPackageTable.Publication_Version_UUID == version_uuid))

        stmt = select(PublicationPackageTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationPackageTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result

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
