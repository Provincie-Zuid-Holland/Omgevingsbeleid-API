from typing import Annotated

from fastapi import Depends

from app.api.domains.publications.dependencies import depends_publication_act_report
from app.api.domains.publications.types.models import PublicationActPackageReport
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationActPackageReportTable
from app.core.tables.users import UsersTable


async def get_detail_act_package_report_endpoint(
    report: Annotated[PublicationActPackageReportTable, Depends(depends_publication_act_report)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_act_package_report,
            )
        ),
    ],
) -> PublicationActPackageReport:
    result: PublicationActPackageReport = PublicationActPackageReport.model_validate(report)
    return result
