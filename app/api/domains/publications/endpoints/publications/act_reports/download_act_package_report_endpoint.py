from typing import Annotated

from fastapi import Depends, Response
from lxml import etree

from app.api.domains.publications.dependencies import depends_publication_act_report
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationActPackageReportTable
from app.core.tables.users import UsersTable


def get_download_act_package_report_endpoint(
    report: Annotated[PublicationActPackageReportTable, Depends(depends_publication_act_report)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_download_publication_act_package_report,
            )
        ),
    ],
) -> Response:
    filename = report.Filename
    content = report.Source_Document

    try:
        xml_tree = etree.fromstring(content, None)
        content = etree.tostring(xml_tree, pretty_print=True).decode()
    except Exception:
        pass

    response = Response(
        content=content,
        media_type="application/xml",
        headers={
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )
    return response
