import uuid
from datetime import date, datetime
from typing import List

from falkordb import FalkorDB
from fastapi import APIRouter, Depends
from rich.pretty import pprint
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session, aliased, selectinload
from sqlalchemy.sql import func, or_

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.db.tables import ObjectsTable
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK


def get_objects(db, timestamp: datetime) -> List[dict]:
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
    result = list(db.scalars(stmt).all())
    return result


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
        db: Session,
        clear: bool,
    ):
        self._db: Session = db
        self._clear: bool = clear

    def handle(self) -> ResponseOK:
        red_db = FalkorDB(host="falkordb", port=6379)
        graph = red_db.select_graph("api")

        if self._clear:
            graph.delete()

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
        object_list = get_objects(self._db, datetime(year=2025, month=2, day=19))

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
        data_properties = ["Code", "Object_Type", "Object_ID", "Title"]

        for code, obj in objects.items():
            # Object Node
            node_type: str = f"Object:{obj.Object_Type.capitalize()}"
            object_identifier: str = f"{projection_id}:{code}"
            object_node_properties = {
                prop: getattr(obj, prop) for prop in node_properties if getattr(obj, prop) is not None
            }
            object_node_properties["identifier"] = object_identifier
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
            data_node_properties["identifier"] = data_identifier
            data_node_properties_parsed: str = ", ".join(
                f"{key}: '{escape_value(value)}'" for key, value in data_node_properties.items()
            )
            create_node_query: str = f"(:{obj.Object_Type.capitalize()}Data {{{data_node_properties_parsed}}})"
            graph_objects.append(create_node_query)

            # Relation: Object -> Data
            relation_query = f"MATCH (o:Object {{identifier: '{object_identifier}'}}), (d:{obj.Object_Type.capitalize()}Data {{identifier: '{data_identifier}'}}) CREATE (o)-[:HAS_DATA]->(d)"
            graph_relation_queries.append(relation_query)

            # Relation: Object -> Hierarchical Object
            if obj.Hierarchy_Code is not None:
                relation_query = f"MATCH (o:Object {{identifier: '{object_identifier}'}}), (ot:Object {{identifier: '{projection_id}:{obj.Hierarchy_Code}'}}) CREATE (o)-[:HAS_HIERARCHY_CODE]->(ot), (ot)-[:REVERSE_HIERARCHY_CODE]->(o)"
                graph_relation_queries.append(relation_query)

            # Relation: Object -> Werkingsgebied
            if obj.Werkingsgebied_Code is not None:
                relation_query = f"MATCH (o:Object {{identifier: '{object_identifier}'}}), (ot:Object {{identifier: '{projection_id}:{obj.Werkingsgebied_Code}'}}) CREATE (o)-[:HAS_WERKINGSGEBIED_CODE]->(ot), (ot)-[:REVERSE_WERKINGSGEBIED_CODE]->(o)"
                graph_relation_queries.append(relation_query)

        print("\n\n")
        pprint(objects)

        print("RUN: create_graph!")

        bulk_create_objects = ",\n\t\t".join(graph_objects)
        create_statement = f"CREATE {bulk_create_objects}"
        print("\n\n\n")
        print(create_statement)
        print("\n\n\n")
        graph.query(create_statement)

        print("\n\n\n")
        print(graph_relation_queries)
        print("\n\n\n")

        for relation_query in graph_relation_queries:
            graph.query(relation_query)

        return ResponseOK(message="OK")

    def update_object(self, identifier: str, properties: dict):
        set_clause = ", ".join(f"{key} = '{escape_value(value)}'" for key, value in properties.items())
        query = f"MATCH (o:Object {{identifier: '{identifier}'}}) SET {set_clause}"
        self.graph.query(query)

    def update_object_data(self, identifier: str, properties: dict):
        set_clause = ", ".join(f"{key} = '{escape_value(value)}'" for key, value in properties.items())
        query = f"MATCH (d:ObjectData {{identifier: '{identifier}'}}) SET {set_clause}"
        self.graph.query(query)

    def remove_relation(self, from_identifier: str, to_identifier: str, relation_type: str):
        query = f"MATCH (a {{identifier: '{from_identifier}'}})-[r:{relation_type}]->(b {{identifier: '{to_identifier}'}}) DELETE r"
        self.graph.query(query)

    def create_relation(self, from_identifier: str, to_identifier: str, relation_type: str):
        query = f"MATCH (a {{identifier: '{from_identifier}'}}), (b {{identifier: '{to_identifier}'}}) CREATE (a)-[:{relation_type}]->(b)"
        self.graph.query(query)


class CreateGraphsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            db: Session = Depends(depends_db),
            clear: bool = False,
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(db, clear)
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Build the graphs",
            description=None,
            tags=["Falkor"],
        )

        return router


class CreateGraphsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "falkor_create"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        return CreateGraphsEndpoint(path)
