from datetime import datetime, timezone
from typing import Annotated, Dict, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from falkordb import Graph

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.graph.dependencies import depends_api_graph
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.types import ModuleStatusCode
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from app.core.tables.users import UsersTable


class Node(BaseModel):
    id: str
    name: str
    object_type: str
    code: str


class Edge(BaseModel):
    source: str
    target: str
    name: str


class ViewResponse(BaseModel):
    nodes: List[Node]
    links: List[Edge]


def get_graph_view_endpoint(
    graph: Annotated[Graph, Depends(depends_api_graph)],
) -> ViewResponse:
    query = """
        MATCH
            (n:Object)
        OPTIONAL MATCH
            (n)-[r:HAS_HIERARCHY_CODE|HAS_WERKINGSGEBIED_CODE]-()
        RETURN
            n, collect(r)
    """
    results = graph.query(query)

    nodes_dict: Dict[str, Node] = {}
    edges_dict: Dict[str, Edge] = {}

    for node, edges in results.result_set:
        node_id: str = str(node.id)
        node_model = Node(
            id=node_id,
            name=node.properties["Title"],
            object_type=node.labels[-1],
            code=node.properties["Code"],
        )
        nodes_dict[node_id] = node_model
        for edge in edges:
            edges_dict[node_id] = Edge(
                source=edge.src_node,
                target=edge.dest_node,
                name=edge.relation,
            )

    response = ViewResponse(
        nodes=list(nodes_dict.values()),
        links=list(edges_dict.values()),
    )

    return response
