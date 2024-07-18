from datetime import datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_zip_by_act_package
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationPackageZipTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class DownloadPackageEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            package_zip: PublicationPackageZipTable = Depends(depends_publication_zip_by_act_package),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_download_publication_act_package,
                ),
            ),
            db: Session = Depends(depends_db),
        ) -> Response:
            return self._handler(
                db,
                user,
                package_zip,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            summary=f"Download a generated publication act package ZIP file",
            description=None,
            tags=["Publication Act Packages"],
        )

        return router

    def _handler(self, db: Session, user: UsersTable, package_zip: PublicationPackageZipTable) -> Response:
        package_zip.Latest_Download_Date = datetime.utcnow()
        package_zip.Latest_Download_By_UUID = user.UUID

        db.add(package_zip)
        db.commit()
        db.flush()

        return Response(
            content=package_zip.Binary,
            media_type="application/x-zip-compressed",
            headers={
                "Access-Control-Expose-Headers": "Content-Disposition",
                "Content-Disposition": f"attachment; filename={package_zip.Filename}",
            },
        )


class DownloadPackageEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "download_publication_act_package"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{act_package_uuid}" in path:
            raise RuntimeError("Missing {act_package_uuid} argument in path")

        return DownloadPackageEndpoint(path=path)
