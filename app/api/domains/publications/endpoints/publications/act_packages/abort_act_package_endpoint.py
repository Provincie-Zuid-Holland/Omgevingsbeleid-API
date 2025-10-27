import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from dependency_injector.wiring import inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_act_package
from app.api.domains.publications.types.enums import (
    PackageType,
    PublicationVersionStatus,
    ReportStatusType,
)
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationEnvironmentTable,
    PublicationVersionTable,
)
from app.core.tables.users import UsersTable


class AbortResponse(BaseModel):
    new_state_uuid: uuid.UUID


@inject
def post_abort_act_package_endpoint(
    act_package: Annotated[PublicationActPackageTable, Depends(depends_publication_act_package)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_abort_publication_act_package,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    confirm: bool = False,
) -> AbortResponse:
    if not confirm:
        raise HTTPException(450, "Are you sure you want to abort this publication?")
    if act_package.Report_Status != ReportStatusType.VALID:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="You can only abort packages which are successfull"
        )
    if act_package.Package_Type != PackageType.PUBLICATION:
        raise HTTPException(451, "Only publications can be aborted")
    if act_package.Used_Environment_State_UUID is None or act_package.Created_Environment_State_UUID is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We do not know what to do if we do not have state uuids",
        )
    timepoint: datetime = datetime.now(timezone.utc)
    since_creation: timedelta = timepoint.date() - act_package.Created_Date.date()
    if since_creation.days > 30:
        raise HTTPException(
            452, "Too many days has passed since creation of the package. Its unlikely that you want to abort this"
        )

    # We can only abort the latest package in the chain:
    # That is, we can only revert the package that caused the current state.
    # After aborting it, we can then abort the package that caused the new (previous) state, and so on...
    publication_version: PublicationVersionTable = act_package.Publication_Version
    environment: PublicationEnvironmentTable = publication_version.Publication.Act.Environment
    if environment.Active_State_UUID != act_package.Created_Environment_State_UUID:
        raise HTTPException(452, "We can only abort the latest package in the state chain")

    act_package.Report_Status = ReportStatusType.ABORTED
    act_package.Modified_Date = timepoint
    act_package.Modified_By_UUID = user.UUID
    session.add(act_package)

    publication_version.Status = PublicationVersionStatus.PUBLICATION_ABORTED
    publication_version.Modified_Date = timepoint
    publication_version.Modified_By_UUID = user.UUID
    session.add(publication_version)

    environment.Active_State_UUID = act_package.Used_Environment_State_UUID
    environment.Modified_Date = timepoint
    environment.Modified_By_UUID = user.UUID
    session.add(environment)

    session.flush()
    session.commit()

    return AbortResponse(
        new_state_uuid=act_package.Used_Environment_State_UUID,
    )
