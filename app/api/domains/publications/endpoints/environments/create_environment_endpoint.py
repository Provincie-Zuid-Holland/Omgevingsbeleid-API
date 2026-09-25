import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.services.state.state import InitialState
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationEnvironmentStateTable, PublicationEnvironmentTable
from app.core.tables.users import UsersTable


class EnvironmentCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: str
    province_id: str
    authority_id: str
    submitter_id: str
    frbr_country: str
    frbr_language: str
    has_state: bool
    can_validate: bool
    can_publicate: bool


class EnvironmentCreatedResponse(BaseModel):
    UUID: uuid.UUID


def post_create_environment_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_environment,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: EnvironmentCreate,
) -> EnvironmentCreatedResponse:
    timepoint: datetime = datetime.now(UTC)

    environment: PublicationEnvironmentTable = PublicationEnvironmentTable(
        id=uuid.uuid4(),
        title=object_in.title,
        description=object_in.description,
        province_id=object_in.province_id,
        authority_id=object_in.authority_id,
        submitter_id=object_in.submitter_id,
        governing_body_type="provinciale_staten",
        frbr_country=object_in.frbr_country,
        frbr_language=object_in.frbr_language,
        is_active=True,
        has_state=object_in.has_state,
        can_validate=object_in.can_validate,
        can_publicate=object_in.can_publicate,
        is_locked=False,
        created_date=timepoint,
        modified_date=timepoint,
        created_by_id=user.UUID,
        modified_by_id=user.UUID,
    )
    session.add(environment)
    session.flush()

    if environment.has_state:
        initial_state = PublicationEnvironmentStateTable(
            id=uuid.uuid4(),
            environment_id=environment.id,
            adjust_on_id=None,
            state=(InitialState().state_dict()),
            is_activated=True,
            activated_datetime=timepoint,
            created_date=timepoint,
            created_by_id=user.UUID,
        )
        session.add(initial_state)
        session.flush()

        environment.active_state_id = initial_state.id
        session.add(environment)

    session.flush()
    session.commit()

    return EnvironmentCreatedResponse(
        UUID=environment.id,
    )
