from typing import Annotated

from fastapi import Depends

from app.api.domains.publications.dependencies import depends_publication_announcement_report
from app.api.domains.publications.types.models import PublicationAnnouncementPackageReport
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationAnnouncementPackageReportTable
from app.core.tables.users import UsersTable


def get_detail_announcement_package_report_endpoint(
    report: Annotated[PublicationAnnouncementPackageReportTable, Depends(depends_publication_announcement_report)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_announcement_package_report,
            )
        ),
    ],
) -> PublicationAnnouncementPackageReport:
    result: PublicationAnnouncementPackageReport = PublicationAnnouncementPackageReport.model_validate(report)
    return result
