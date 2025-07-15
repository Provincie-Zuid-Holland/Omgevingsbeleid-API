import uuid
from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationAreaOfJurisdictionTable
from app.core.tables.users import UsersTable


class AOJCreate(BaseModel):
    Administrative_Borders_ID: str = Field(..., min_length=3)
    Administrative_Borders_Domain: str = Field(..., min_length=3)
    Administrative_Borders_Date: date


class AOJCreatedResponse(BaseModel):
    UUID: uuid.UUID


def post_create_aoj_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_aoj,
            )
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: AOJCreate,
) -> AOJCreatedResponse:
    area_of_jurisdiction = PublicationAreaOfJurisdictionTable(
        UUID=uuid.uuid4(),
        Administrative_Borders_ID=object_in.Administrative_Borders_ID,
        Administrative_Borders_Domain=object_in.Administrative_Borders_Domain,
        Administrative_Borders_Date=object_in.Administrative_Borders_Date,
        Created_Date=datetime.now(timezone.utc),
        Created_By_UUID=user.UUID,
    )

    session.add(area_of_jurisdiction)
    session.flush()
    session.commit()

    return AOJCreatedResponse(
        UUID=area_of_jurisdiction.UUID,
    )
