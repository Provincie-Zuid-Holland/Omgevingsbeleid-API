from datetime import date
from typing import Annotated, Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from pytest import Session

from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_area_of_jurisdiction
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationAreaOfJurisdictionTable
from app.core.tables.users import UsersTable


class AOJEdit(BaseModel):
    Administrative_Borders_ID: Optional[str] = None
    Administrative_Borders_Domain: Optional[str] = None
    Administrative_Borders_Date: Optional[date] = None

def post_edit_aoj_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_aoj,
            )
        ),
    ],
    area_of_jurisdiction: Annotated[PublicationAreaOfJurisdictionTable, Depends(depends_publication_area_of_jurisdiction)],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: AOJEdit,
) -> ResponseOK:
    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        setattr(area_of_jurisdiction, key, value)
    
    session.add(area_of_jurisdiction)
    session.commit()
    session.flush()

    return ResponseOK(message="OK")
