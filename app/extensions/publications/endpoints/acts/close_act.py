from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.publications.dependencies import depends_publication_act_active
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationActTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        act: PublicationActTable,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._act: PublicationActTable = act

    def handle(self) -> ResponseOK:
        self._act.Modified_By_UUID = self._user.UUID
        self._act.Modified_Date = datetime.utcnow()
        self._act.Is_Active = False

        self._db.add(self._act)
        self._db.commit()
        self._db.flush()

        return ResponseOK(
            message="OK",
        )


class ClosePublicationActEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_close_publication_act,
                ),
            ),
            act: PublicationActTable = Depends(depends_publication_act_active),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                act,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Close publication act",
            description=None,
            tags=["Publication Acts"],
        )

        return router


class ClosePublicationActEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "close_publication_act"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{act_uuid}" in path:
            raise RuntimeError("Missing {act_uuid} argument in path")

        return ClosePublicationActEndpoint(
            path=path,
        )
