import uuid
from datetime import UTC, datetime
from typing import Annotated

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
from app.api.domains.publications.types.enums import MutationStrategy, PublicationVersionStatus
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.modules import ModuleStatusHistoryTable
from app.core.tables.publications import PublicationTable, PublicationVersionTable
from app.core.tables.users import UsersTable


class PublicationVersionCreate(BaseModel):
    Module_Status_ID: int
    Mutation_Strategy: MutationStrategy = MutationStrategy.RENVOOI


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
        publication.module_id,
        object_in.Module_Status_ID,
    )

    bill_metadata = defaults_provider.get_bill_metadata(publication.document_type, publication.procedure_type)
    bill_compact = defaults_provider.get_bill_compact(publication.document_type, publication.procedure_type)
    procedural = defaults_provider.get_procedural()

    # no active status for stateless/internal publication
    status = PublicationVersionStatus.NOT_APPLICABLE
    if publication.environment.has_state:
        status = PublicationVersionStatus.ACTIVE

    timepoint: datetime = datetime.now(UTC)
    version: PublicationVersionTable = PublicationVersionTable(
        id=uuid.uuid4(),
        publication_id=publication.id,
        module_status_id=module_status.id,
        bill_metadata=bill_metadata.model_dump(),
        bill_compact=bill_compact.model_dump(),
        procedural=procedural.model_dump(),
        effective_date=None,
        announcement_date=None,
        is_locked=False,
        status=status,
        mutation_strategy=object_in.Mutation_Strategy,
        created_date=timepoint,
        modified_date=timepoint,
        created_by_id=user.UUID,
        modified_by_id=user.UUID,
    )

    session.add(version)
    session.flush()
    session.commit()

    return PublicationVersionCreatedResponse(
        UUID=version.id,
    )


def _guard_locked(publication: PublicationTable):
    if not publication.module.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This module is not active")
    if not publication.act.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This act can no longer be used")


def _get_module_status(
    session: Session, module_status_repository: ModuleStatusRepository, module_id: int, status_id: int
) -> ModuleStatusHistoryTable:
    module_status: ModuleStatusHistoryTable | None = module_status_repository.get_by_id(
        session,
        module_id,
        status_id,
    )
    if module_status is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module Status niet gevonden")
    return module_status
