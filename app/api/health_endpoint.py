from datetime import datetime, timezone
from typing import Annotated

import sqlalchemy
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from app.api.api_container import ApiContainer
from app.core.db.session import SessionFactoryType, session_scope_with_context

build_datetime: datetime = datetime.now(timezone.utc)


@inject
def health_check(
    db_session_factory: Annotated[SessionFactoryType, Depends(Provide[ApiContainer.db_session_factory])],
):
    health_info = {
        "status": "healthy",
        "database": "ok",
        "version": "11",
        "build": str(build_datetime),
    }

    try:
        with session_scope_with_context(db_session_factory) as session:
            session.close()
    except sqlalchemy.exc.SQLAlchemyError:
        health_info["status"] = "unhealthy"
        health_info["database"] = "not connected"

    if health_info["status"] == "unhealthy":
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, health_info)

    return health_info
