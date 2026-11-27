from datetime import UTC, datetime, timedelta
from typing import Annotated

import sqlalchemy
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy import text

from app.api.api_container import ApiContainer
from app.core.db.session import AsyncSessionFactoryType, async_session_scope

build_datetime: datetime = datetime.now(UTC)


@inject
async def health_check(
    db_session_factory: Annotated[AsyncSessionFactoryType, Depends(Provide[ApiContainer.db_session_factory])],
    lifetime: Annotated[timedelta, Depends(Provide[ApiContainer.access_token_lifetime])],
):
    health_info = {
        "status": "healthy",
        "database": "ok",
        "version": "11",
        "build": str(build_datetime),
        "lt": str(lifetime),
    }

    try:
        async with async_session_scope(db_session_factory) as session:
            await session.execute(text("SELECT 1"))
    except sqlalchemy.exc.SQLAlchemyError:
        health_info["status"] = "unhealthy"
        health_info["database"] = "not connected"

    if health_info["status"] == "unhealthy":
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, health_info)

    return health_info
