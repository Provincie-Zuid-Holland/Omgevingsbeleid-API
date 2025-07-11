from datetime import datetime, timezone
from dependency_injector.wiring import inject
from fastapi import HTTPException, status

build_datetime: datetime = datetime.now(timezone.utc)


@inject
async def health_check(
    # db_session_factory: Annotated[sessionmaker, Depends(ApiContainer.db_session_factory)],
):
    health_info = {
        "status": "healthy",
        "database": "ok",
        "version": "11",
        "build": str(build_datetime),
    }

    # @todo
    # try:
    #     session: Session = init_db_session(db_session_factory)
    #     session.close()
    # except sqlalchemy.exc.SQLAlchemyError:
    #     health_info["status"] = "unhealthy"
    #     health_info["database"] = "not connected"

    if health_info["status"] == "unhealthy":
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, health_info)

    return health_info
