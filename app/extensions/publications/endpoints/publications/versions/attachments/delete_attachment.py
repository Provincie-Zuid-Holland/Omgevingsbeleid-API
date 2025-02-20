from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.publications.dependencies import depends_publication_version, depends_publication_version_attachment
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationVersionAttachmentTable, PublicationVersionTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        version: PublicationVersionTable,
        attachment: PublicationVersionAttachmentTable,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._version: PublicationVersionTable = version
        self._attachment: PublicationVersionAttachmentTable = attachment

    def handle(self) -> ResponseOK:
        self._guard()

        # @todo: This should become a soft delete but I could not upgrade the database at this point
        self._db.delete(self._attachment.File)
        self._db.delete(self._attachment)
        self._db.commit()
        self._db.flush()

        return ResponseOK(message="Attachment deleted")

    def _guard(self):
        if self._attachment.Publication_Version_UUID != self._version.UUID:
            raise HTTPException(
                status_code=409, detail="You can not delete an attachment of another publication version"
            )
        if not self._version.Publication.Act.Is_Active:
            raise HTTPException(status_code=409, detail="This act can no longer be used")
        if self._version.Is_Locked:
            raise HTTPException(status_code=409, detail="This publication version is locked")


class DeletePublicationVersionAttachmentEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            version: PublicationVersionTable = Depends(depends_publication_version),
            attachment: PublicationVersionAttachmentTable = Depends(depends_publication_version_attachment),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_edit_publication_version,
                )
            ),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                version,
                attachment,
            )
            response: ResponseOK = handler.handle()
            return response

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["DELETE"],
            summary=f"Delete a publication version attachment",
            response_model=ResponseOK,
            description=None,
            tags=["Publication Versions"],
        )

        return router


class DeletePublicationVersionAttachmentEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "delete_publication_version_attachment"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{version_uuid}" in path:
            raise RuntimeError("Missing {version_uuid} argument in path")
        if not "{attachment_id}" in path:
            raise RuntimeError("Missing {attachment_id} argument in path")

        return DeletePublicationVersionAttachmentEndpoint(path=path)
