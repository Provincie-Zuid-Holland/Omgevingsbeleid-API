from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.storage_files.db.tables import StorageFileTable
from app.extensions.storage_files.dependencies import depends_storage_file
from app.extensions.storage_files.models.models import StorageFileBasic


class DetailStorageFileEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            storage_file: StorageFileTable = Depends(depends_storage_file),
        ) -> StorageFileBasic:
            result: StorageFileBasic = StorageFileBasic.model_validate(storage_file)
            return result

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=StorageFileBasic,
            summary=f"Get storage file details",
            description=None,
            tags=["Storage File"],
        )

        return router


class DetailStorageFileEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "detail_storage_file"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{file_uuid}" in path:
            raise RuntimeError("Missing {file_uuid} argument in path")

        return DetailStorageFileEndpoint(path)
