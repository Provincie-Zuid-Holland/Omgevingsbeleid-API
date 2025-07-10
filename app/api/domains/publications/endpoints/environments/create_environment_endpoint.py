import uuid
from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.publications.services.state.state import InitialState
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationEnvironmentStateTable, PublicationEnvironmentTable
from app.core.tables.users import UsersTable


class EnvironmentCreate(BaseModel):
    Title: str = Field(..., min_length=3)
    Description: str
    Province_ID: str
    Authority_ID: str
    Submitter_ID: str
    Frbr_Country: str
    Frbr_Language: str
    Has_State: bool
    Can_Validate: bool
    Can_Publicate: bool


class EnvironmentCreatedResponse(BaseModel):
    UUID: uuid.UUID


@inject
def post_create_environment_endpoint(
    object_in: Annotated[EnvironmentCreate, Depends()],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_environment,
            )
        ),
    ],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
) -> EnvironmentCreatedResponse:
    timepoint: datetime = datetime.now(timezone.utc)

    environment: PublicationEnvironmentTable = PublicationEnvironmentTable(
        UUID=uuid.uuid4(),
        Title=object_in.Title,
        Description=object_in.Description,
        Province_ID=object_in.Province_ID,
        Authority_ID=object_in.Authority_ID,
        Submitter_ID=object_in.Submitter_ID,
        Governing_Body_Type="provinciale_staten",
        Frbr_Country=object_in.Frbr_Country,
        Frbr_Language=object_in.Frbr_Language,
        Is_Active=True,
        Has_State=object_in.Has_State,
        Can_Validate=object_in.Can_Validate,
        Can_Publicate=object_in.Can_Publicate,
        Is_Locked=False,
        Created_Date=timepoint,
        Modified_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_By_UUID=user.UUID,
    )
    db.add(environment)
    db.flush()

    if environment.Has_State:
        initial_state = PublicationEnvironmentStateTable(
            UUID=uuid.uuid4(),
            Environment_UUID=environment.UUID,
            Adjust_On_UUID=None,
            State=(InitialState().state_dict()),
            Is_Activated=True,
            Activated_Datetime=timepoint,
            Created_Date=timepoint,
            Created_By_UUID=user.UUID,
        )
        db.add(initial_state)
        db.flush()

        environment.Active_State_UUID = initial_state.UUID
        db.add(environment)

    db.flush()
    db.commit()

    return EnvironmentCreatedResponse(
        UUID=environment.UUID,
    )
