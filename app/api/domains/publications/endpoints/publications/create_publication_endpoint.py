import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

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
    document_type: DocumentType
    procedure_type: ProcedureType
    template_id: uuid.UUID
    environment_id: uuid.UUID
    act_id: int


class PublicationCreatedResponse(BaseModel):
    id: uuid.UUID


@inject
async def post_create_publication_endpoint(
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
    session: Annotated[AsyncSession, Depends(depends_db_session)],
    object_in: PublicationCreate,
) -> PublicationCreatedResponse:
    timepoint: datetime = datetime.now(UTC)

    module: ModuleTable = await _get_module(session, module_repository, object_in.module_id)
    if not module.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This module is not active")

    template: PublicationTemplateTable = await _get_template(
        session, template_repository, object_in.template_id, object_in.document_type
    )
    environment: PublicationEnvironmentTable = await _get_environment(
        session, environment_repository, object_in.environment_id
    )
    act: PublicationActTable = await _get_act(session, act_repository, object_in)

    publication = PublicationTable(
        id=uuid.uuid4(),
        module_id=module.module_id,
        document_type=object_in.document_type.value,
        procedure_type=object_in.procedure_type.value,
        template_id=template.id,
        environment_id=environment.id,
        act_id=act.id,
        is_locked=False,
        created_date=timepoint,
        modified_date=timepoint,
        created_by_id=user.id,
        modified_by_id=user.id,
    )

    session.add(publication)
    await session.flush()
    await session.commit()

    return PublicationCreatedResponse(
        id=publication.id,
    )


async def _get_module(session: AsyncSession, repository: ModuleRepository, module_id: int) -> ModuleTable:
    module: ModuleTable | None = await repository.get_by_id(session, module_id)
    if module is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module niet gevonden")
    if module.closed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module is gesloten")

    return module


async def _get_template(
    session: AsyncSession,
    repository: PublicationTemplateRepository,
    template_id: uuid.UUID,
    document_type: DocumentType,
) -> PublicationTemplateTable:
    template: PublicationTemplateTable | None = await repository.get_by_id(session, template_id)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template niet gevonden")
    if not template.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template is gesloten")
    if template.document_type != document_type.value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template hoort niet bij dit document type")
    return template


async def _get_environment(
    session: AsyncSession, repository: PublicationEnvironmentRepository, environment_id: uuid.UUID
) -> PublicationEnvironmentTable:
    environment: PublicationEnvironmentTable | None = await repository.get_by_id(
        session,
        environment_id,
    )
    if environment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Environment niet gevonden")
    if not environment.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Environment is in actief")
    return environment


async def _get_act(
    session: AsyncSession, repository: PublicationActRepository, object_in: PublicationCreate
) -> PublicationActTable:
    act: PublicationActTable | None = await repository.get_by_id(session, object_in.act_id)
    if act is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act niet gevonden")
    if not act.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act is in actief")
    if act.environment_id != object_in.environment_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act is van een ander Environment")
    if act.document_type != object_in.document_type.value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act is van een ander Document Type")
    return act
