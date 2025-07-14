from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import PackageType
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.publications import PublicationActPackageTable


class PublicationActPackageRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuid: UUID) -> Optional[PublicationActPackageTable]:
        stmt = select(PublicationActPackageTable).filter(PublicationActPackageTable.UUID == uuid)
        return self.fetch_first(session, stmt)

    def get_by_act_version(self, session: Session, act_version_uuid: UUID) -> Optional[PublicationActPackageTable]:
        stmt = select(PublicationActPackageTable).filter(
            PublicationActPackageTable.Act_Version_UUID == act_version_uuid
        )
        result: Optional[PublicationActPackageTable] = self.fetch_first(session, stmt)
        return result

    def get_with_filters(
        self,
        session: Session,
        pagination: SortedPagination,
        version_uuid: Optional[UUID] = None,
        package_type: Optional[PackageType] = None,
    ) -> PaginatedQueryResult:
        filters = []
        if version_uuid is not None:
            filters.append(and_(PublicationActPackageTable.Publication_Version_UUID == version_uuid))

        if package_type is not None:
            filters.append(and_(PublicationActPackageTable.Package_Type == package_type.value))

        stmt = select(PublicationActPackageTable).filter(*filters)

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(pagination.sort.column, pagination.sort.order),
        )
        return paged_result
