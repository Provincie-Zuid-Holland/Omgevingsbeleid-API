import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
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
    Module_ID: int
    Title: str
    Document_Type: DocumentType
    Procedure_Type: ProcedureType
    Template_UUID: uuid.UUID
    Environment_UUID: uuid.UUID
    Act_UUID: uuid.UUID


class PublicationCreatedResponse(BaseModel):
    UUID: uuid.UUID


@inject
def post_create_publication(
    object_in: Annotated[PublicationCreate, Depends()],
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
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
) -> PublicationCreatedResponse:
    timepoint: datetime = datetime.now(timezone.utc)

    module: ModuleTable = _get_module(module_repository, object_in.Module_ID)
    template: PublicationTemplateTable = _get_template(
        template_repository, object_in.Template_UUID, object_in.Document_Type
    )
    environment: PublicationEnvironmentTable = _get_environment(environment_repository, object_in.Environment_UUID)
    act: PublicationActTable = _get_act(act_repository, object_in)

    publication = PublicationTable(
        UUID=uuid.uuid4(),
        Module_ID=module.Module_ID,
        Title=object_in.Title,
        Document_Type=object_in.Document_Type.value,
        Procedure_Type=object_in.Procedure_Type.value,
        Template_UUID=template.UUID,
        Environment_UUID=environment.UUID,
        Act_UUID=act.UUID,
        Is_Locked=False,
        Created_Date=timepoint,
        Modified_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_By_UUID=user.UUID,
    )

    db.add(publication)
    db.commit()
    db.flush()

    return PublicationCreatedResponse(
        UUID=publication.UUID,
    )


def _get_module(repository: ModuleRepository, module_id: int) -> ModuleTable:
    module: Optional[ModuleTable] = repository.get_by_id(module_id)
    if module is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module niet gevonden")
    if module.Closed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module is gesloten")

    return module


def _get_template(
    repository: PublicationTemplateRepository,
    template_uuid: uuid.UUID,
    document_type: DocumentType,
) -> PublicationTemplateTable:
    template: Optional[PublicationTemplateTable] = repository.get_by_uuid(template_uuid)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template niet gevonden")
    if not template.Is_Active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template is gesloten")
    if template.Document_Type != document_type.value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template hoort niet bij dit document type")
    return template


def _get_environment(
    repository: PublicationEnvironmentRepository, environment_uuid: uuid.UUID
) -> PublicationEnvironmentTable:
    environment: Optional[PublicationEnvironmentTable] = repository.get_by_uuid(
        environment_uuid,
    )
    if environment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Environment niet gevonden")
    if not environment.Is_Active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Environment is in actief")
    return environment


def _get_act(repository: PublicationActRepository, object_in: PublicationCreate) -> PublicationActTable:
    act: Optional[PublicationActTable] = repository.get_by_uuid(object_in.Act_UUID)
    if act is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act niet gevonden")
    if not act.Is_Active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act is in actief")
    if act.Environment_UUID != object_in.Environment_UUID:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act is van een ander Environment")
    if act.Document_Type != object_in.Document_Type.value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Act is van een ander Document Type")
    return act
