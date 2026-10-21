import uuid
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from app.api.domains.publications.dependencies import depends_publication_announcement_package
from app.api.domains.publications.types.models import PackageZipShort
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationAnnouncementPackageTable,
    PublicationEnvironmentTable,
    PublicationVersionTable,
)
from app.core.tables.users import UsersTable


class PublicationAnnouncementPackageDetailResponse(BaseModel):
    id: uuid.UUID
    package_type: str
    report_status: str
    delivery_id: str
    document_type: str

    announcement_id: uuid.UUID
    doc_version_id: uuid.UUID | None
    zip: PackageZipShort
    created_environment_state_id: uuid.UUID | None
    used_environment_state_id: uuid.UUID | None

    created_date: datetime
    modified_date: datetime
    created_by_id: uuid.UUID
    modified_by_id: uuid.UUID

    module_id: int | None
    module_title: str | None
    module_status_id: int | None
    module_status_status: str | None
    environment_id: uuid.UUID
    environment_title: str

    model_config = ConfigDict(from_attributes=True)


def get_detail_announcement_package_endpoint(
    announcement_package: Annotated[
        PublicationAnnouncementPackageTable, Depends(depends_publication_announcement_package)
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_announcement_package,
            )
        ),
    ],
) -> PublicationAnnouncementPackageDetailResponse:
    act_package: PublicationActPackageTable = announcement_package.announcement.act_package
    publication_version: PublicationVersionTable = act_package.publication_version
    module: ModuleTable | None = act_package.module
    module_status: ModuleStatusHistoryTable | None = act_package.module_status
    environment: PublicationEnvironmentTable = publication_version.publication.environment
    zip: PackageZipShort = PackageZipShort.model_validate(announcement_package.zip)

    result = PublicationAnnouncementPackageDetailResponse(
        id=announcement_package.id,
        package_type=announcement_package.package_type,
        report_status=announcement_package.report_status,
        delivery_id=announcement_package.delivery_id,
        document_type=publication_version.publication.document_type,
        announcement_id=announcement_package.announcement_id,
        doc_version_id=announcement_package.doc_version_id,
        zip=zip,
        created_environment_state_id=announcement_package.created_environment_state_id,
        used_environment_state_id=announcement_package.used_environment_state_id,
        created_date=announcement_package.created_date,
        modified_date=announcement_package.modified_date,
        created_by_id=announcement_package.created_by_id,
        modified_by_id=announcement_package.modified_by_id,
        module_id=module.module_id if module else None,
        module_title=module.title if module else None,
        module_status_id=module_status.id if module_status else None,
        module_status_status=module_status.status if module_status else None,
        environment_id=environment.id,
        environment_title=environment.title,
    )

    return result
