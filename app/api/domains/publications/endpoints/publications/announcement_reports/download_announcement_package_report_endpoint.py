import contextlib
from typing import Annotated

from fastapi import Depends, Response
from lxml import etree

from app.api.domains.publications.dependencies import depends_publication_announcement_report
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationAnnouncementPackageReportTable
from app.core.tables.users import UsersTable


async def get_download_announcement_package_report_endpoint(
    report: Annotated[PublicationAnnouncementPackageReportTable, Depends(depends_publication_announcement_report)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_download_publication_announcement_package_report,
            )
        ),
    ],
) -> Response:
    content = report.source_document
    filename = report.filename

    # We try to make it pretty, but it's not required for the response to work
    with contextlib.suppress(etree.XMLSyntaxError):
        parser = etree.XMLParser(encoding="utf-8")
        xml_tree = etree.fromstring(content.encode("utf-8"), parser)
        content = etree.tostring(xml_tree, pretty_print=True).decode()

    response = Response(
        content=content,
        media_type="application/xml",
        headers={
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )
    return response
