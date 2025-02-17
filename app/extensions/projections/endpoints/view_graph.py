from typing import Dict, List

from falkordb import FalkorDB
from fastapi import APIRouter
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver


class Node(BaseModel):
    id: str
    name: str
    object_type: str


class Edge(BaseModel):
    source: str
    target: str
    name: str


class ViewResponse(BaseModel):
    nodes: List[Node]
    links: List[Edge]


class EndpointHandler:
    def handle(self) -> ViewResponse:
        red_db = FalkorDB(host="falkordb", port=6379)
        graph = red_db.select_graph("api")

        query = "MATCH (n:Object) OPTIONAL MATCH (n)-[r:HIERARCHY|HAS_GEBIED]-() RETURN n, collect(r)"
        results = graph.query(query)

        nodes_dict: Dict[int, Node] = {}
        edges_dict: Dict[str, Edge] = {}

        for node, edges in results.result_set:
            nodes_dict[node.id] = Node(
                id=node.id,
                name=node.properties["Title"],
                object_type=node.labels[-1],
            )
            for edge in edges:
                edges_dict[edge.id] = Edge(
                    source=edge.src_node,
                    target=edge.dest_node,
                    name=edge.relation,
                )

        response = ViewResponse(
            nodes=list(nodes_dict.values()),
            links=list(edges_dict.values()),
        )

        return response


class ViewGraphEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler() -> ViewResponse:
            handler: EndpointHandler = EndpointHandler()
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=ViewResponse,
            summary=f"View the graph",
            description=None,
            tags=["Falkor"],
        )

        return router


class ViewGraphEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "falkor_view"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        return ViewGraphEndpoint(path)
