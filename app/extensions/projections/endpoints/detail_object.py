from datetime import datetime
from typing import Optional

from falkordb import FalkorDB
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver


class WerkingsgebiedBasic(BaseModel):
    Object_ID: int
    Object_Type: str
    Code: str
    Title: str
    Start_Validity: Optional[datetime]
    End_Validity: Optional[datetime]


class DetailObject(BaseModel):
    Object_ID: int
    Object_Type: str
    Code: str
    Title: str
    Start_Validity: Optional[datetime]
    End_Validity: Optional[datetime]

    Werkingsgebied: Optional[WerkingsgebiedBasic] = Field(None)


class DetailResponse(BaseModel):
    Object: Optional[DetailObject]


class EndpointHandler:
    def __init__(self, node_id: str):
        self._node_id: str = node_id
        self._falkor = FalkorDB(host="falkordb", port=6379).select_graph("api")

    def handle(self) -> DetailResponse:
        query = """
            MATCH
                (n:Object {identifier: $identifier})
            OPTIONAL MATCH
                (n)-[r:HAS_WERKINGSGEBIED_CODE]->(wg:Object)
            RETURN n, wg
        """
        params = {"identifier": self._node_id}
        results = self._falkor.query(query, params)

        if not results.result_set:
            return DetailResponse(Object=None)

        node_data = results.result_set[0][0]
        wg_data = results.result_set[0][1]

        detail_object = DetailObject(**node_data.properties)
        if wg_data:
            detail_object.Werkingsgebied = WerkingsgebiedBasic(**wg_data.properties)

        response = DetailResponse(
            Object=detail_object,
        )

        return response


class DetailObjectEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_type: str,
            lineage_id: int,
        ) -> DetailResponse:
            publication_id: str = "3"
            node_id: str = f"{publication_id}:{object_type}-{lineage_id}"

            handler: EndpointHandler = EndpointHandler(
                node_id=node_id,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=DetailResponse,
            summary=f"Detail object",
            description=None,
            tags=["Falkor"],
        )

        return router


class DetailObjectEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "falkor_detail_object"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{object_type}" in path:
            raise RuntimeError("Missing {object_type} argument in path")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return DetailObjectEndpoint(
            path=path,
        )
