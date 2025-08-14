import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .enums import DocumentType, PackageType, ReportStatusType


class PublicationPackageFilters(BaseModel):
	document_type: Optional[DocumentType] = None
	package_type: Optional[PackageType] = None
	status_filter: Optional[ReportStatusType] = None
	environment_uuid: Optional[uuid.UUID] = None
	model_config = ConfigDict(from_attributes=True) 