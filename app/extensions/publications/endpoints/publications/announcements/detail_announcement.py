from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_announcement
from app.extensions.publications.models.models import PublicationAnnouncement
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationAnnouncementTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class DetailPublicationAnnouncementEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            announcement: PublicationAnnouncementTable = Depends(depends_publication_announcement),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_announcement,
                )
            ),
        ) -> PublicationAnnouncement:
            result: PublicationAnnouncement = PublicationAnnouncement.from_orm(announcement)
            return result

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PublicationAnnouncement,
            summary=f"Get details of a publication announcement",
            description=None,
            tags=["Publication Announcements"],
        )

        return router


class DetailPublicationAnnouncementEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "detail_publication_announcement"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        if not "{announcement_uuid}" in path:
            raise RuntimeError("Missing {announcement_uuid} argument in path")

        return DetailPublicationAnnouncementEndpoint(path=path)
