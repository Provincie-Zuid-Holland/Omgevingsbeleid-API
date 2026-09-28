import uuid
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, ConfigDict

from app.api.domains.publications.dependencies import depends_publication_act_package
from app.api.domains.publications.types.models import PackageZipShort
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from app.core.tables.publications import PublicationActPackageTable, PublicationEnvironmentTable, PublicationTable
from app.core.tables.users import UsersTable


class PublicationActPackageDetailResponse(BaseModel):
    id: uuid.UUID
    package_type: str
    report_status: str
    delivery_id: str
    document_type: str

    publication_version_id: uuid.UUID
    bill_version_id: uuid.UUID | None
    act_version_id: uuid.UUID | None
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


def get_detail_act_package_endpoint(
    act_package: Annotated[PublicationActPackageTable, Depends(depends_publication_act_package)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_act_package,
            )
        ),
    ],
) -> PublicationActPackageDetailResponse:
    publication: PublicationTable = act_package.publication_version.publication
    module: ModuleTable | None = act_package.module
    module_status: ModuleStatusHistoryTable | None = act_package.module_status
    environment: PublicationEnvironmentTable = publication.environment
    zip: PackageZipShort = PackageZipShort.model_validate(act_package.zip)

    result = PublicationActPackageDetailResponse(
        id=act_package.id,
        package_type=act_package.package_type,
        report_status=act_package.report_status,
        delivery_id=act_package.delivery_id,
        document_type=publication.document_type,
        publication_version_id=act_package.publication_version_id,
        bill_version_id=act_package.bill_version_id,
        act_version_id=act_package.act_version_id,
        zip=zip,
        created_environment_state_id=act_package.created_environment_state_id,
        used_environment_state_id=act_package.used_environment_state_id,
        created_date=act_package.created_date,
        modified_date=act_package.modified_date,
        created_by_id=act_package.created_by_id,
        modified_by_id=act_package.modified_by_id,
        module_id=module.module_id if module else None,
        module_title=module.title if module else None,
        module_status_id=module_status.id if module_status else None,
        module_status_status=module_status.status if module_status else None,
        environment_id=environment.id,
        environment_title=environment.title,
    )

    return result
