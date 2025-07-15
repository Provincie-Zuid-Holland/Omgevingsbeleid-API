import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

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
    Environment_UUID: uuid.UUID
    Document_Type: DocumentType
    Title: str
    Work_Other: Optional[str] = None


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
        session, environment_repository, object_in.Environment_UUID
    )

    metadata = defaults_provider.get_metadata(object_in.Document_Type.value)
    work_other: str = object_in.Work_Other or _get_work_other(session, object_in)

    timepoint: datetime = datetime.now(timezone.utc)
    act: PublicationActTable = PublicationActTable(
        UUID=uuid.uuid4(),
        Environment_UUID=environment.UUID,
        Document_Type=object_in.Document_Type.value,
        Title=object_in.Title,
        Is_Active=True,
        Metadata=metadata.model_dump(),
        Metadata_Is_Locked=False,
        Work_Province_ID=environment.Province_ID,
        Work_Country=environment.Frbr_Country,
        Work_Date=str(timepoint.year),
        Work_Other=work_other,
        Withdrawal_Purpose_UUID=None,
        Created_Date=timepoint,
        Modified_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_By_UUID=user.UUID,
    )

    session.add(act)
    session.commit()
    session.flush()

    return ActCreatedResponse(
        UUID=act.UUID,
    )


def _get_environment(
    session: Session,
    repository: PublicationEnvironmentRepository,
    environment_uuid: uuid.UUID,
) -> PublicationEnvironmentTable:
    environment: Optional[PublicationEnvironmentTable] = repository.get_by_uuid(
        session,
        environment_uuid,
    )
    if environment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Environment niet gevonden")
    if not environment.Is_Active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication Environment is in actief")

    return environment


def _get_work_other(
    session: Session,
    object_in: ActCreate,
) -> str:
    stmt = (
        select(func.count())
        .select_from(PublicationActTable)
        .filter(PublicationActTable.Environment_UUID == object_in.Environment_UUID)
        .filter(PublicationActTable.Document_Type == object_in.Document_Type.value)
        .filter(
            or_(
                PublicationActTable.Procedure_Type == ProcedureType.FINAL,
                PublicationActTable.Procedure_Type.is_(None),
            ).self_group()
        )
    )
    count: int = (session.execute(stmt).scalar() or 0) + 1
    id_suffix: str = f"{count}"

    work_other: str = f"{object_in.Document_Type.value.lower()}-{id_suffix}"
    return work_other
