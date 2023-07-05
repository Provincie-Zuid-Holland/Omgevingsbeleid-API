from typing import List
import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.core.dependencies import depends_db
from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.dependencies import depends_pagination

from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.dynamic.utils.pagination import Pagination, PagedResponse, query_paginated


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


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        pagination: Pagination,
        query: str,
    ):
        self._db: Session = db
        self._pagination: Pagination = pagination
        self._query: str = query

    def handle(self) -> PagedResponse[SearchObject]:
        if self._db.bind.name in ["sqlite", "mssql"]:
            stmt = self._like_search_stmt()
        else:
            stmt = self._match_search_stmt()

        # table_rows = self._db.execute(stmt).all()
        table_rows, total_count = query_paginated(
            query=stmt,
            session=self._db,
            limit=self._pagination.limit,
            offset=self._pagination.offset,
        )

        search_objects: List[SearchObject] = [
            SearchObject.parse_obj(r._asdict()) for r in table_rows
        ]

        return PagedResponse[SearchObject](
            total=total_count,
            limit=self._pagination.limit,
            offset=self._pagination.offset,
            results=search_objects,
        )

    def _like_search_stmt(self):
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
        )
        return stmt

    def _match_search_stmt(self):
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
                ObjectsTable.Title.match(self._query)
                | ObjectsTable.Description.match(self._query)
            )
            .order_by(
                desc(
                    ObjectsTable.Title.match(self._query)
                    + ObjectsTable.Description.match(self._query)
                )
            )
            .order_by(desc(ObjectsTable.Modified_Date))
        )
        return stmt


class SearchEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            query: str,
            db: Session = Depends(depends_db),
            pagination: Pagination = Depends(depends_pagination),
        ) -> PagedResponse[SearchObject]:
            handler: EndpointHandler = EndpointHandler(
                db,
                pagination,
                query,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[SearchObject],
            summary=f"Search for objects",
            description=None,
            tags=["Search"],
        )

        return router


class SearchEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "search"

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

        return SearchEndpoint(
            path=path,
        )
