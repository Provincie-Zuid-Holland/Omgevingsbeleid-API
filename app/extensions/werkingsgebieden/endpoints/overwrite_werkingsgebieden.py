from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session
from app.core.dependencies import depends_db

from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.utils.response import ResponseOK
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import depends_current_active_user
from app.extensions.werkingsgebieden.db.tables import ObjectWerkingsgebiedenTable
from app.extensions.werkingsgebieden.models.models import WerkingsgebiedShort


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_type: str,
        lineage_id: int,
        overwrite_list: List[WerkingsgebiedShort],
    ):
        self._db: Session = db
        self._object_code: str = f"{object_type}-{lineage_id}"
        self._overwrite_list: List[WerkingsgebiedShort] = overwrite_list

    def handle(self) -> ResponseOK:
        try:
            self._remove_current_werkingsgebieden()
            self._create_werkingsgebieden()
            self._db.commit()

            return ResponseOK(
                message="OK",
            )
        except Exception as e:
            self._db.rollback()
            raise e

    def _remove_current_werkingsgebieden(self):
        stmt = delete(ObjectWerkingsgebiedenTable).filter(
            ObjectWerkingsgebiedenTable.Object_Code == self._object_code
        )
        self._db.execute(stmt)

    def _create_werkingsgebieden(self):
        if not self._overwrite_list:
            return

        for data in self._overwrite_list:
            object_werkingsgebied: ObjectWerkingsgebiedenTable = (
                ObjectWerkingsgebiedenTable(
                    Object_Code=self._object_code,
                    Werkingsgebied_UUID=data.UUID,
                    Description=data.Description,
                )
            )
            self._db.add(object_werkingsgebied)


class OverwriteWerkingsgebiedenEndpoint(Endpoint):
    def __init__(
        self,
        converter: Converter,
        endpoint_id: str,
        path: str,
        object_id: str,
        object_type: str,
    ):
        self._converter: Converter = converter
        self._endpoint_id: str = endpoint_id
        self._path: str = path
        self._object_id: str = object_id
        self._object_type: str = object_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            overwrite_list: List[WerkingsgebiedShort],
            user: GebruikersTable = Depends(depends_current_active_user),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                self._object_type,
                lineage_id,
                overwrite_list,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["PUT"],
            response_model=ResponseOK,
            summary=f"Overwrite all werkingsgebieden of the given {self._object_type} lineage",
            description=None,
            tags=[self._object_type],
        )

        return router


class OverwriteWerkingsgebiedenEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "overwrite_werkingsgebieden"

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
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return OverwriteWerkingsgebiedenEndpoint(
            converter=converter,
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
        )
