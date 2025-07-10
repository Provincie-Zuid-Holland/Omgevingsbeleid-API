import uuid
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_simple_pagination
from app.api.domains.publications.repository.publication_announcement_report_repository import (
    PublicationAnnouncementReportRepository,
)
from app.api.domains.publications.types.enums import ReportStatusType
from app.api.domains.publications.types.models import PublicationAnnouncementPackageReportShort
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.utils.pagination import PagedResponse, SimplePagination
from app.core.tables.users import UsersTable


@inject
def get_list_annnouncement_package_reports_endpoint(
    announcement_package_uuid: Annotated[Optional[uuid.UUID], None],
    report_status: Annotated[Optional[ReportStatusType], None],
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    report_repository: Annotated[
        PublicationAnnouncementReportRepository,
        Depends(Provide[ApiContainer.publication.announcement_report_repository]),
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_announcement_package_report,
            )
        ),
    ],
) -> PagedResponse[PublicationAnnouncementPackageReportShort]:
    paginated_result = report_repository.get_with_filters(
        announcement_package_uuid=announcement_package_uuid,
        report_status=report_status,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    results = [PublicationAnnouncementPackageReportShort.model_validate(r) for r in paginated_result.items]

    return PagedResponse[PublicationAnnouncementPackageReportShort](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
