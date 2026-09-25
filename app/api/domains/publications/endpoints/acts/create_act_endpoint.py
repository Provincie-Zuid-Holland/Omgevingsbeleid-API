import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.repository.publication_environment_repository import PublicationEnvironmentRepository
from app.api.domains.publications.services.act_defaults_provider import ActDefaultsProvider
from app.api.domains.publications.types.enums import DocumentType, ProcedureType
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationActTable, PublicationEnvironmentTable
from app.core.tables.users import UsersTable


class ActCreate(BaseModel):
    environment_id: uuid.UUID
    document_type: DocumentType
    title: str
    work_other: str | None = None


class ActCreatedResponse(BaseModel):
    UUID: uuid.UUID


@inject
def post_create_act_endpoint(
    environment_repository: Annotated[
        PublicationEnvironmentRepository, Depends(Provide[ApiContainer.publication.environment_repository])
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_act,
            )
        ),
    ],
    defaults_provider: Annotated[ActDefaultsProvider, Depends(Provide[ApiContainer.publication.act_defaults_provider])],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: ActCreate,
) -> ActCreatedResponse:
    environment: PublicationEnvironmentTable = _get_environment(
        session, environment_repository, object_in.environment_id
    )

    meta_data = defaults_provider.get_metadata(object_in.document_type.value)
    work_other: str = object_in.work_other or _get_work_other(session, object_in)

    timepoint: datetime = datetime.now(UTC)
    act: PublicationActTable = PublicationActTable(
        id=uuid.uuid4(),
        environment_id=environment.id,
        document_type=object_in.document_type.value,
        title=object_in.title,
        is_active=True,
        meta_data=meta_data.model_dump(),
        meta_data_is_locked=False,
        work_province_id=environment.province_id,
        work_country=environment.frbr_country,
        work_date=str(timepoint.year),
        work_other=work_other,
        withdrawal_purpose_id=None,
        created_date=timepoint,
        modified_date=timepoint,
        created_by_id=user.UUID,
        modified_by_id=user.UUID,
    )

    session.add(act)
    session.flush()
    session.commit()

    return ActCreatedResponse(
        UUID=act.uuid,
    )


def _get_environment(
    session: Session,
    repository: PublicationEnvironmentRepository,
    environment_uuid: uuid.UUID,
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


def _get_work_other(
    session: Session,
    object_in: ActCreate,
) -> str:
    stmt = (
        select(func.count())
        .select_from(PublicationActTable)
        .filter(PublicationActTable.environment_id == object_in.environment_id)
        .filter(PublicationActTable.document_type == object_in.document_type.value)
        .filter(
            or_(
                PublicationActTable.procedure_type == ProcedureType.FINAL,
                PublicationActTable.procedure_type.is_(None),
            ).self_group()
        )
    )
    count: int = (session.execute(stmt).scalar() or 0) + 1
    id_suffix: str = f"{count}"

    work_other: str = f"{object_in.document_type.value.lower()}-{id_suffix}"
    return work_other
