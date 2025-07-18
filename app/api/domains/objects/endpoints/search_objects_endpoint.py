import uuid
from typing import Annotated, List

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session, depends_simple_pagination
from app.api.utils.pagination import PagedResponse, PaginatedQueryResult, SimplePagination, query_paginated
from app.core.tables.objects import ObjectsTable


class SearchObject(BaseModel):
    Object_Type: str
    Object_ID: int
    UUID: uuid.UUID
    Title: str
    Description: str

    @field_validator("Title", "Description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    model_config = ConfigDict(validate_assignment=True)


class EndpointHandler:
    def __init__(
        self,
        session: Session,
        pagination: SimplePagination,
        query: str,
    ):
        self._session: Session = session
        self._pagination: SimplePagination = pagination
        self._query: str = query

    def handle(self) -> PagedResponse[SearchObject]:
        if self._session.bind.name in ["sqlite", "mssql"]:
            stmt = self._like_search_stmt()
        else:
            stmt = self._match_search_stmt()

        # table_rows = self._db.execute(stmt).all()
        result: PaginatedQueryResult = query_paginated(
            query=stmt,
            session=self._session,
            limit=self._pagination.limit,
            offset=self._pagination.offset,
        )

        search_objects: List[SearchObject] = [SearchObject.model_validate(r._asdict()) for r in result.items]

        return PagedResponse[SearchObject](
            total=result.total_count,
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
            .filter(ObjectsTable.Title.like(like_query) | ObjectsTable.Description.like(like_query))
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
            .filter(ObjectsTable.Title.match(self._query) | ObjectsTable.Description.match(self._query))
            .order_by(desc(ObjectsTable.Title.match(self._query) + ObjectsTable.Description.match(self._query)))
            .order_by(desc(ObjectsTable.Modified_Date))
        )
        return stmt


def get_search_objects_endpoint(
    query: str,
    session: Annotated[Session, Depends(depends_db_session)],
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
) -> PagedResponse[SearchObject]:
    handler: EndpointHandler = EndpointHandler(
        session,
        pagination,
        query,
    )
    return handler.handle()
