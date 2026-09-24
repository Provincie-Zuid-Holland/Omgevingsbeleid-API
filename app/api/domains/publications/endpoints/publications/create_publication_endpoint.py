import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.repositories.module_repository import ModuleRepository
from app.api.domains.publications.repository.publication_act_repository import PublicationActRepository
from app.api.domains.publications.repository.publication_environment_repository import PublicationEnvironmentRepository
from app.api.domains.publications.repository.publication_template_repository import PublicationTemplateRepository
from app.api.domains.publications.types.enums import DocumentType, ProcedureType
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.modules import ModuleTable
from app.core.tables.publications import (
    PublicationActTable,
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationTemplateTable,
)
from app.core.tables.users import UsersTable


class PublicationCreate(BaseModel):
    module_id: int
    Document_Type: DocumentType
    Procedure_Type: ProcedureType
    Template_UUID: uuid.UUID
    Environment_UUID: uuid.UUID
    Act_UUID: uuid.UUID


class PublicationCreatedResponse(BaseModel):
    UUID: uuid.UUID


@inject
def post_create_publication_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication,
            )
        ),
    ],
    module_repository: Annotated[ModuleRepository, Depends(Provide[ApiContainer.module_repository])],
    template_repository: Annotated[
        PublicationTemplateRepository, Depends(Provide[ApiContainer.publication.template_repository])
    ],
    environment_repository: Annotated[
        PublicationEnvironmentRepository, Depends(Provide[ApiContainer.publication.environment_repository])
    ],
    act_repository: Annotated[PublicationActRepository, Depends(Provide[ApiContainer.publication.act_repository])],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: PublicationCreate,
) -> PublicationCreatedResponse:
    timepoint: datetime = datetime.now(UTC)

    module: ModuleTable = _get_module(session, module_repository, object_in.module_id)
    if not module.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This module is not active")

    template: PublicationTemplateTable = _get_template(
        session, template_repository, object_in.Template_UUID, object_in.Document_Type
    )
    environment: PublicationEnvironmentTable = _get_environment(
        session, environment_repository, object_in.Environment_UUID
    )
    act: PublicationActTable = _get_act(session, act_repository, object_in)

    publication = PublicationTable(
        id=uuid.uuid4(),
        module_id=module.module_id,
        document_type=object_in.Document_Type.value,
        procedure_type=object_in.Procedure_Type.value,
        template_id=template.id,
        environment_id=environment.id,
        act_id=act.uuid,
        is_locked=False,
        created_date=timepoint,
        modified_date=timepoint,
        created_by_id=user.UUID,
        modified_by_id=user.UUID,
    )

    session.add(publication)
    session.flush()
    session.commit()

    return PublicationCreatedResponse(
        UUID=publication.id,
    )


def _get_module(session: Session, repository: ModuleRepository, module_id: int) -> ModuleTable:
    module: ModuleTable | None = repository.get_by_id(session, module_id)
    if module is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module niet gevonden")
    if module.closed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module is gesloten")

    return module


def _get_template(
    session: Session,
    repository: PublicationTemplateRepository,
    template_uuid: uuid.UUID,
    document_type: DocumentType,
) -> PublicationTemplateTable:
    template: PublicationTemplateTable | None = repository.get_by_uuid(session, template_uuid)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template niet gevonden")
    if not template.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template is gesloten")
    if template.document_type != document_type.value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template hoort niet bij dit document type")
    return template


def _get_environment(
    session: Session, repository: PublicationEnvironmentRepository, environment_uuid: uuid.UUID
) -> PublicationEnvironmentTable:
    environment: PublicationEnvironmentTable | None = repository.get_by_uuid(
        session,
        environment_uuid,
    )
    if environment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Environment niet gevonden")
    if not environment.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Environment is in actief")
    return environment


def _get_act(
    session: Session, repository: PublicationActRepository, object_in: PublicationCreate
) -> PublicationActTable:
    act: PublicationActTable | None = repository.get_by_uuid(session, object_in.Act_UUID)
    if act is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act niet gevonden")
    if not act.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act is in actief")
    if act.environment_id != object_in.Environment_UUID:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act is van een ander Environment")
    if act.document_type != object_in.Document_Type.value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act is van een ander Document Type")
    return act
