from typing import Optional
from uuid import UUID

from sqlalchemy import and_

from app.api.domains.publications.types.filters import PublicationPackageFilters
from app.api.types import Selectable


def apply_package_overview_filters(
	query: Selectable,
	publication_alias,
	package_alias,
	filters: Optional[PublicationPackageFilters] = None,
	package_uuid: Optional[UUID] = None,
) -> Selectable:
	conditions = []

	if filters and filters.document_type is not None:
		conditions.append(publication_alias.Document_Type == filters.document_type.value)

	if filters and filters.package_type is not None:
		conditions.append(package_alias.Package_Type == filters.package_type.value)

	if filters and filters.status_filter is not None:
		conditions.append(package_alias.Report_Status == filters.status_filter)

	if filters and filters.environment_uuid is not None:
		conditions.append(publication_alias.Environment_UUID == filters.environment_uuid)

	if package_uuid is not None:
		conditions.append(package_alias.UUID == package_uuid)

	if conditions:
		query = query.filter(and_(*conditions))

	return query 