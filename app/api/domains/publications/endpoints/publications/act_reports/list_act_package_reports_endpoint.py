import uuid
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_simple_pagination
from app.api.domains.publications.repository.publication_act_report_repository import PublicationActReportRepository
from app.api.domains.publications.types.enums import ReportStatusType
from app.api.domains.publications.types.models import PublicationActPackageReportShort
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.utils.pagination import PagedResponse, SimplePagination
from app.core.tables.users import UsersTable


@inject
def get_list_act_package_reports_endpoint(
    act_package_uuid: Annotated[Optional[uuid.UUID], None],
    report_status: Annotated[Optional[ReportStatusType], None],
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    report_repository: Annotated[
        PublicationActReportRepository, Depends(Provide[ApiContainer.publication.act_report_repository])
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_act_package_report,
            )
        ),
    ],
) -> PagedResponse[PublicationActPackageReportShort]:
    paginated_result = report_repository.get_with_filters(
        act_package_uuid=act_package_uuid,
        report_status=report_status,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    results: List[PublicationActPackageReportShort] = [
        PublicationActPackageReportShort.model_validate(r) for r in paginated_result.items
    ]

    return PagedResponse[PublicationActPackageReportShort](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
