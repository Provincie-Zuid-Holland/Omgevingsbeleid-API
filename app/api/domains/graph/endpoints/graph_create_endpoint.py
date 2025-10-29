from datetime import datetime, timezone, date
from typing import Annotated, Dict, List
import uuid

from rich.pretty import pprint
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, aliased, selectinload
from sqlalchemy import func, desc, select, or_
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
from app.core.tables.objects import ObjectsTable
from app.core.tables.users import UsersTable


def escape_value(value):
    if isinstance(value, str):
        return value.replace("'", "\\'")
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, date):
        return value.isoformat()
    elif isinstance(value, uuid.UUID):
        return str(value)
    return value


class EndpointHandler:
    def __init__(
        self,
        session: Session,
        graph: Graph,
        clear: bool,
    ):
        self._session: Session = session
        self._graph: Graph = graph
        self._clear: bool = clear

    def handle(self) -> ResponseOK:
        if self._clear:
            self._graph.delete()

        graph_objects = []
        graph_relation_queries = []

        # 2023-06-05 14:00:18.517
        # projection_id: str = "1"
        # object_list = get_objects(self._db, datetime(year=2023, month=6, day=8))

        # 2024-10-01 00:00:00
        # projection_id: str = "2"
        # object_list = get_objects(self._db, datetime(year=2024, month=10, day=1))

        # 2025-02-19 00:00:00
        projection_id: str = "3"
        object_list = self._get_objects(datetime(year=2025, month=2, day=19))

        objects = {o.Code: o for o in object_list}

        node_properties = [
            "Code",
            "Object_Type",
            "Object_ID",
            "Start_Validity",
            "End_Validity",
            "Modified_Date",
            "Title",
        ]
        data_properties = [
            "Code",
            "Object_Type",
            "Object_ID",
            "Title",
            "Description",
            "Cause",
            "Provincial_Interest",
            "Explanation",
            "Role",
            "Effect",
        ]

        for code, obj in objects.items():
            # Object Node
            node_type: str = f"Object:{obj.Object_Type.capitalize()}"
            object_identifier: str = f"{projection_id}:{code}"
            object_node_properties = {
                prop: getattr(obj, prop) for prop in node_properties if getattr(obj, prop) is not None
            }
            object_node_properties["_identifier"] = object_identifier
            object_node_properties_parsed: str = ", ".join(
                f"{key}: '{escape_value(value)}'" for key, value in object_node_properties.items()
            )
            create_node_query: str = f"(:{node_type} {{{object_node_properties_parsed}}})"
            graph_objects.append(create_node_query)

            # Data Node
            data_identifier: str = f"{projection_id}:{code}:data"
            data_node_properties = {
                prop: getattr(obj, prop) for prop in data_properties if getattr(obj, prop) is not None
            }
            data_node_properties["_identifier"] = data_identifier
            data_node_properties_parsed: str = ", ".join(
                f"{key}: '{escape_value(value)}'" for key, value in data_node_properties.items()
            )
            create_node_query: str = f"(:ObjectData {{{data_node_properties_parsed}}})"
            graph_objects.append(create_node_query)

            # Relation: Object -> Data
            relation_query = f"MATCH (o:Object {{_identifier: '{object_identifier}'}}), (d:ObjectData {{_identifier: '{data_identifier}'}}) CREATE (o)-[:HAS_DATA]->(d)"
            graph_relation_queries.append(relation_query)

            # Relation: Object -> Hierarchical Object
            if obj.Hierarchy_Code is not None:
                relation_query = f"MATCH (o:Object {{_identifier: '{object_identifier}'}}), (ot:Object {{_identifier: '{projection_id}:{obj.Hierarchy_Code}'}}) CREATE (o)-[:HAS_HIERARCHY_CODE]->(ot), (ot)-[:REVERSE_HIERARCHY_CODE]->(o)"
                graph_relation_queries.append(relation_query)

            # Relation: Object -> Werkingsgebied
            if obj.Werkingsgebied_Code is not None:
                relation_query = f"MATCH (o:Object {{_identifier: '{object_identifier}'}}), (ot:Object {{_identifier: '{projection_id}:{obj.Werkingsgebied_Code}'}}) CREATE (o)-[:HAS_WERKINGSGEBIED_CODE]->(ot), (ot)-[:REVERSE_WERKINGSGEBIED_CODE]->(o)"
                graph_relation_queries.append(relation_query)

        print("\n\n")
        pprint(objects)

        print("RUN: create_graph!")

        bulk_create_objects = ",\n\t\t".join(graph_objects)
        create_statement = f"CREATE {bulk_create_objects}"
        print("\n\n\n")
        print(create_statement)
        print("\n\n\n")
        self._graph.query(create_statement)

        print("\n\n\n")
        print(graph_relation_queries)
        print("\n\n\n")

        for relation_query in graph_relation_queries:
            self._graph.query(relation_query)

        return ResponseOK(message="OK")


    def _get_objects(self, timestamp: datetime) -> List[dict]:
        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.Code,
                order_by=desc(ObjectsTable.Modified_Date),
            )
            .label("_RowNumber")
        )

        subq = (
            select(ObjectsTable, row_number)
            .options(selectinload(ObjectsTable.ObjectStatics))
            .join(ObjectsTable.ObjectStatics)
            .filter(ObjectsTable.Start_Validity <= timestamp)
        )

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_objects)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > timestamp,
                    subq.c.End_Validity == None,
                )
            )
            .order_by(desc(subq.c.Modified_Date))
        )
        result = list(self._session.scalars(stmt).all())
        return result

    def _update_object(self, identifier: str, properties: dict):
        set_clause = ", ".join(f"{key} = '{escape_value(value)}'" for key, value in properties.items())
        query = f"MATCH (o:Object {{_identifier: '{identifier}'}}) SET {set_clause}"
        self._graph.query(query)

    def _update_object_data(self, identifier: str, properties: dict):
        set_clause = ", ".join(f"{key} = '{escape_value(value)}'" for key, value in properties.items())
        query = f"MATCH (d:ObjectData {{_identifier: '{identifier}'}}) SET {set_clause}"
        self._graph.query(query)

    def _remove_relation(self, from_identifier: str, to_identifier: str, relation_type: str):
        query = f"MATCH (a {{_identifier: '{from_identifier}'}})-[r:{relation_type}]->(b {{_identifier: '{to_identifier}'}}) DELETE r"
        self._graph.query(query)

    def _create_relation(self, from_identifier: str, to_identifier: str, relation_type: str):
        query = f"MATCH (a {{_identifier: '{from_identifier}'}}), (b {{_identifier: '{to_identifier}'}}) CREATE (a)-[:{relation_type}]->(b)"
        self._graph.query(query)



@inject
def post_graph_create_endpoint(
    session: Annotated[Session, Depends(depends_db_session)],
    graph: Annotated[Graph, Depends(depends_api_graph)],
    clear: bool = False,
) -> ResponseOK:
    handler = EndpointHandler(session, graph, clear)
    return handler.handle()
