from typing import List, Optional
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator
from sqlalchemy import desc, select, func, text
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.dependencies import depends_pagination
from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.utils.pagination import Pagination
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter


class SearchRequest(BaseModel):
    UUIDS: List[uuid.UUID] = []
    Object_Types: List[str] = []
    Query: Optional[str] = None
    Owner: Optional[uuid.UUID] = None

    Offset: Optional[int] = None
    Limit: Optional[int] = None

    def is_empty(self) -> bool:
        return not any([
            self.UUIDS,
            self.Object_Types,
            self.Query,
            self.Owner,
        ])


class SearchObject(BaseModel):
    Object_Type: str
    Object_ID: int
    UUID: uuid.UUID
    Title: str
    Description: str

    @validator("Title", "Description", pre=True)
    def default_empty_string(cls, v):
        return v or ""

    class Config:
        validate_assignment = True


class SearchResponse(BaseModel):
    Objects: List[SearchObject]


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_in: SearchRequest,
    ):
        self._db: Session = db
        self._object_in: SearchRequest = object_in

    def handle(self) -> SearchResponse:
        if self._object_in.is_empty():
            raise ValueError("Missing search filters")

        stmt = text(
            f"""
                SELECT
                    UUID
                FROM (
                    SELECT
                        UUID,
                        End_Validity,
                        ROW_NUMBER() OVER (
                            PARTITION BY
                                Code
                            ORDER BY
                                Modified_Date DESC
                        ) AS _RowNumber
                    FROM
                        {ObjectsTable.__table__}
                    WHERE
                        Start_Validity <= GETDATE()
                ) AS valid_subquery
                WHERE
                    _RowNumber = 1
                    AND End_Validity > GETDATE()
            """
        )

        # Valid objects
        subq = (
            select(
                ObjectsTable,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.Code,
                    order_by=desc(ObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ObjectsTable)
            .filter(ObjectsTable.Start_Validity <= datetime.now())
            .subquery()
        )


        stmt = self._search_stmt()
        table_rows = self._db.execute(stmt).all()
        search_objects: List[SearchObject] = [
            SearchObject.parse_obj(r._asdict()) for r in table_rows
        ]

        return SearchResponse(
            Objects=search_objects,
        )

    def _search_stmt(self):
        like_query = f"%{self._query}%"
        stmt = (
            select(
                ObjectsTable.Object_Type,
                ObjectsTable.Object_ID,
                ObjectsTable.UUID,
                ObjectsTable.Title,
                ObjectsTable.Description,
            )   
            .select_from(ObjectsTable)
            .filter(
                ObjectsTable.Title.like(like_query)
                | ObjectsTable.Description.like(like_query)
            )
            .order_by(desc(ObjectsTable.Modified_Date))
            .limit(self._pagination.get_limit())
            .offset(self._pagination.get_offset())
        )
        return stmt


class MssqlValidSearchEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: SearchRequest,
            db: Session = Depends(depends_db),
        ) -> SearchResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=SearchResponse,
            summary=f"Search for valid objects",
            description=None,
            tags=["Search"],
        )

        return router


class MssqlValidSearchEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "mssql_valid_search"

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

        return MssqlValidSearchEndpoint(
            path=path,
        )
