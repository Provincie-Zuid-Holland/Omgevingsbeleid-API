from datetime import date, datetime, timezone
from typing import Annotated, Any, Dict, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.publications.dependencies import depends_publication_version
from app.api.domains.publications.services.publication_version_validator import PublicationVersionValidator
from app.api.domains.publications.types.models import BillCompact, BillMetadata, Procedural
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationVersionTable
from app.core.tables.users import UsersTable

ProceduralClass = Procedural


class PublicationVersionEdit(BaseModel):
    Module_Status_ID: Optional[int] = None
    Effective_Date: Optional[date] = None
    Announcement_Date: Optional[date] = None

    Bill_Metadata: Optional[BillMetadata] = None
    Bill_Compact: Optional[BillCompact] = None
    Procedural: Optional[ProceduralClass] = None


class PublicationVersionEditResponse(BaseModel):
    Errors: List[dict]
    Is_Valid: bool


@inject
def post_edit_version_endpoint(
    object_in: Annotated[PublicationVersionEdit, Depends()],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_version,
            )
        ),
    ],
    version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    validator: Annotated[PublicationVersionValidator, Depends(Provide[ApiContainer.publication.version_validator])],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
) -> PublicationVersionEditResponse:
    _guard_locked(version)

    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        if isinstance(value, BaseModel):
            value = value.model_dump()
        setattr(version, key, value)

    version.Modified_By_UUID = user.UUID
    version.Modified_Date = datetime.now(timezone.utc)

    db.add(version)
    db.commit()
    db.flush()

    errors: List[dict] = validator.get_errors(version)
    is_valid: bool = len(errors) == 0

    return PublicationVersionEditResponse(
        Errors=errors,
        Is_Valid=is_valid,
    )


def _guard_locked(version: PublicationVersionTable):
    if not version.Publication.Act.Is_Active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This act can no longer be used")
