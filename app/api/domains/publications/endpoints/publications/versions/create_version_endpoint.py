import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.repositories.module_status_repository import ModuleStatusRepository
from app.api.domains.publications.dependencies import depends_publication
from app.api.domains.publications.services.publication_version_defaults_provider import (
    PublicationVersionDefaultsProvider,
)
from app.api.domains.publications.types.enums import PublicationVersionStatus
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.modules import ModuleStatusHistoryTable
from app.core.tables.publications import PublicationTable, PublicationVersionTable
from app.core.tables.users import UsersTable


class PublicationVersionCreate(BaseModel):
    Module_Status_ID: int


class PublicationVersionCreatedResponse(BaseModel):
    UUID: uuid.UUID


@inject
def post_create_version_endpoint(
    publication: Annotated[PublicationTable, Depends(depends_publication)],
    module_status_repository: Annotated[
        ModuleStatusRepository, Depends(Provide[ApiContainer.module_status_repository])
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_version,
            )
        ),
    ],
    defaults_provider: Annotated[
        PublicationVersionDefaultsProvider, Depends(Provide[ApiContainer.publication.version_defaults_provider])
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: PublicationVersionCreate,
) -> PublicationVersionCreatedResponse:
    _guard_locked(publication)

    module_status: ModuleStatusHistoryTable = _get_module_status(
        session,
        module_status_repository,
        publication.Module_ID,
        object_in.Module_Status_ID,
    )

    bill_metadata = defaults_provider.get_bill_metadata(publication.Document_Type, publication.Procedure_Type)
    bill_compact = defaults_provider.get_bill_compact(publication.Document_Type, publication.Procedure_Type)
    procedural = defaults_provider.get_procedural()

    # no active status for stateless/internal publication
    status = PublicationVersionStatus.NOT_APPLICABLE
    if publication.Environment.Has_State:
        status = PublicationVersionStatus.ACTIVE

    timepoint: datetime = datetime.now(timezone.utc)
    version: PublicationVersionTable = PublicationVersionTable(
        UUID=uuid.uuid4(),
        Publication_UUID=publication.UUID,
        Module_Status_ID=module_status.ID,
        Bill_Metadata=bill_metadata.model_dump(),
        Bill_Compact=bill_compact.model_dump(),
        Procedural=procedural.model_dump(),
        Effective_Date=None,
        Announcement_Date=None,
        Is_Locked=False,
        Status=status,
        Created_Date=timepoint,
        Modified_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_By_UUID=user.UUID,
    )

    session.add(version)
    session.commit()
    session.flush()

    return PublicationVersionCreatedResponse(
        UUID=version.UUID,
    )


def _guard_locked(publication: PublicationTable):
    if not publication.Act.Is_Active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This act can no longer be used")


def _get_module_status(
    session: Session, module_status_repository: ModuleStatusRepository, module_id: int, status_id: int
) -> ModuleStatusHistoryTable:
    module_status: Optional[ModuleStatusHistoryTable] = module_status_repository.get_by_id(
        session,
        module_id,
        status_id,
    )
    if module_status is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module Status niet gevonden")
    return module_status
