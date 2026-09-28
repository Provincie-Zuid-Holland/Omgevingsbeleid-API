import uuid
from datetime import UTC, date, datetime
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
    administrative_borders_id: str = Field(..., min_length=3)
    administrative_borders_domain: str = Field(..., min_length=3)
    administrative_borders_date: date


class AOJCreatedResponse(BaseModel):
    id: uuid.UUID


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
        id=uuid.uuid4(),
        administrative_borders_id=object_in.administrative_borders_id,
        administrative_borders_domain=object_in.administrative_borders_domain,
        administrative_borders_date=object_in.administrative_borders_date,
        created_date=datetime.now(UTC),
        created_by_id=user.UUID,
    )

    session.add(area_of_jurisdiction)
    session.flush()
    session.commit()

    return AOJCreatedResponse(
        id=area_of_jurisdiction.id,
    )
