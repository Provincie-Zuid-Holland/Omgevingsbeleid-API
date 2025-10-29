from datetime import datetime, timezone
from typing import Annotated, Dict, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
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



class WerkingsgebiedBasic(BaseModel):
    Object_ID: int
    Object_Type: str
    Code: str
    Title: str
    Start_Validity: Optional[datetime]
    End_Validity: Optional[datetime]


class MaatregelFull(BaseModel):
    Object_ID: int
    Object_Type: str
    Code: str
    Title: str
    Start_Validity: Optional[datetime]
    End_Validity: Optional[datetime]

    Werkingsgebied: Optional[WerkingsgebiedBasic] = Field(None)


class DetailResponse(BaseModel):
    Object: Optional[MaatregelFull]



def get_graph_detail_object_endpoint(
    graph: Annotated[Graph, Depends(depends_api_graph)],
    object_type: str,
    lineage_id: int,
) -> DetailResponse:
    publication_id: str = "3"
    node_id: str = f"{publication_id}:{object_type}-{lineage_id}"

    query = """
        MATCH
            (n:Object {_identifier: $identifier})
        OPTIONAL MATCH
            (n)-[odr:HAS_DATA]->(od:ObjectData)
        OPTIONAL MATCH
            (n)-[wgr:HAS_WERKINGSGEBIED_CODE]->(wg:Object)
        RETURN n, od, wg
    """
    params = {"identifier": node_id}
    # results = self._falkor.profile(query, params)
    results = graph.query(query, params)

    if not results.result_set:
        return DetailResponse(Object=None)

    node = results.result_set[0][0]
    node_data = results.result_set[0][1]
    wg = results.result_set[0][2]

    detail_object = DetailObject(**(node.properties | node_data.properties))
    detail_object.Data = node.properties | node_data.properties
    if wg:
        detail_object.Werkingsgebied = WerkingsgebiedBasic(**wg.properties)

    response = DetailResponse(
        Object=detail_object,
    )

    return response
