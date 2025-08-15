from datetime import datetime
import uuid
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.publications.services.unified_packages_provider import UnifiedPackagesProvider
from app.api.domains.publications.types.enums import PackageType, ReportStatusType, DocumentType, PublicationType
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.utils.pagination import OptionalSortedPagination, OrderConfig, PagedResponse, Sort, SortedPagination
from app.core.tables.users import UsersTable


class ListUnifiedPackagesEndpointContext(BaseEndpointContext):
    order_config: OrderConfig


class UnifiedPackage(BaseModel):
    Publication_Type: str
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Package_Type: str
    Report_Status: str
    Delivery_ID: str
    Module_ID: int
    Module_Title: str
    Document_Type: str
    Environment_UUID: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


@inject
def get_list_unified_packages_endpoint(
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    session: Annotated[Session, Depends(depends_db_session)],
    unified_packages_provider: Annotated[
        UnifiedPackagesProvider, Depends(Provide[ApiContainer.publication.unified_packages_provider])
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_unified_packages,
            )
        ),
    ],
    context: Annotated[ListUnifiedPackagesEndpointContext, Depends()],
    environment_uuid: Optional[uuid.UUID] = None,
    module_id: Optional[int] = None,
    report_status: Optional[ReportStatusType] = ReportStatusType.VALID,
    package_type: Optional[PackageType] = PackageType.PUBLICATION,
    document_type: Optional[DocumentType] = None,
    publication_type: Optional[PublicationType] = None,
) -> PagedResponse[UnifiedPackage]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    paginated_result = unified_packages_provider.get_unified_packages(
        session=session,
        pagination=pagination,
        environment_uuid=environment_uuid,
        module_id=module_id,
        report_status=report_status,
        package_type=package_type,
        document_type=document_type,
        publication_type=publication_type,
    )

    results: List[UnifiedPackage] = [UnifiedPackage.model_validate(item) for item in paginated_result.items]

    return PagedResponse[UnifiedPackage](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=results,
    )
