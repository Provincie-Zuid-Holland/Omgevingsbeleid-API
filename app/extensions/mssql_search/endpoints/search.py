from typing import List, Optional
import uuid
import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator
from sqlalchemy import text
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from app.core.dependencies import depends_db
from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.dependencies import depends_pagination
from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.utils.pagination import Pagination, PagedResponse
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class SearchConfig(BaseModel):
    searchable_columns_high: List[str]
    searchable_columns_low: List[str]


class SearchObject(BaseModel):
    Module_ID: Optional[int]
    UUID: uuid.UUID
    Object_Type: str
    Object_ID: int
    Title: str
    Description: str
    Score: float

    @validator("Title", "Description", pre=True)
    def default_empty_string(cls, v):
        return v or ""

    class Config:
        validate_assignment = True


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        search_config: SearchConfig,
        pagination: Pagination,
        query: str,
    ):
        self._db: Session = db
        self._search_config: SearchConfig = search_config
        self._pagination: Pagination = pagination
        self._query: str = query

    def handle(self) -> PagedResponse[SearchObject]:
        if not len(self._query):
            raise ValueError("Missing search query")
        if '\\' in json.dumps(self._query):
            raise ValueError("Invalid search characters")
        if self._pagination.get_limit() > 50:
            raise ValueError("Pagination limit is too high")

        stmt = text(
            f"""
                WITH valid_uuids (Module_ID, UUID, Object_Type, Object_ID, Title, Description)
                AS
                (
                    SELECT
                        0 AS Module_ID,
                        UUID,
                        Object_Type,
                        Object_ID,
                        Title,
                        Description
                    FROM (
                        SELECT
                            UUID,
                            Object_Type,
                            Object_ID,
                            Title,
                            Description,
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
                        AND (End_Validity > GETDATE() OR End_Validity IS NULL)
                    
                    UNION

                    SELECT
                        Module_ID,
                        UUID,
                        Object_Type,
                        Object_ID,
                        Title,
                        Description
                    FROM (
                        SELECT
                            mo.Module_ID,
                            mo.UUID,
                            mo.Object_Type,
                            mo.Object_ID,
                            mo.Title,
                            mo.Description,
                            ROW_NUMBER() OVER (
                                PARTITION BY
                                    mo.Code
                                ORDER BY
                                    mo.Modified_Date DESC
                            ) AS _RowNumber
                        FROM
                            {ModuleObjectsTable.__table__} AS mo
                            INNER JOIN {ModuleTable.__table__} AS m ON mo.Module_ID = m.Module_ID
                        WHERE
                            m.Closed = 0
                    ) AS module_subquery
                    WHERE
                        _RowNumber = 1
                )

                SELECT
                    v.Module_ID,
                    v.UUID,
                    v.Object_Type,
                    v.Object_ID,
                    v.Title,
                    v.Description,
                    s.WeightedRank AS _Rank,
                    COUNT(*) OVER() AS _Total_Count
                FROM valid_uuids AS v
                INNER JOIN
                (
                    SELECT
                        [KEY],
                        SUM(Rank) as WeightedRank
                    FROM
                    (
                        SELECT Rank * 1 as Rank, [KEY] from CONTAINSTABLE({ObjectsTable.__table__}, ({", ".join(self._search_config.searchable_columns_high)}), :query)
                            UNION
                        SELECT Rank * 0.5 as Rank, [KEY] from CONTAINSTABLE({ObjectsTable.__table__}, ({", ".join(self._search_config.searchable_columns_low)}), :query)
                            UNION

                        SELECT Rank * 1 as Rank, [KEY] from CONTAINSTABLE({ModuleObjectsTable.__table__}, ({", ".join(self._search_config.searchable_columns_high)}), :query)
                            UNION
                        SELECT Rank * 0.5 as Rank, [KEY] from CONTAINSTABLE({ModuleObjectsTable.__table__}, ({", ".join(self._search_config.searchable_columns_low)}), :query)
                    ) AS x
                    GROUP BY [KEY]
                ) AS s ON s.[KEY] = v.UUID
                ORDER BY
                    s.WeightedRank DESC
                OFFSET
                    :offset ROWS 
                FETCH
                    NEXT :limit ROWS ONLY
            """
        )

        stmt = stmt.bindparams(
            query=f'"{self._query}"',
            offset=self._pagination.get_offset,
            limit=self._pagination.get_limit,
        )

        results = self._db.execute(stmt)
        search_objects: List[SearchObject] = []
        total_count: int = 0

        for row in results:
            row = row._asdict()

            description: str = ""
            if row["Description"]:
                try:
                    soup = BeautifulSoup(row["Description"], "html.parser")
                    description = soup.get_text()
                except:
                    pass

            search_object: SearchObject = SearchObject(
                Module_ID=row["Module_ID"] if row["Module_ID"] else None,
                UUID=row["UUID"],
                Object_Type=row["Object_Type"],
                Object_ID=row["Object_ID"],
                Title=row["Title"],
                Description=description,
                Score=row["_Rank"],
            )
            search_objects.append(search_object)
            total_count = row["_Total_Count"]

        return PagedResponse[SearchObject](
            total=total_count,
            offset=self._pagination.get_offset,
            limit=self._pagination.get_limit,
            results=search_objects,
        )


class MssqlSearchEndpoint(Endpoint):
    def __init__(self, path: str, search_config: SearchConfig):
        self._path: str = path
        self._search_config: SearchConfig = search_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            query: str,
            db: Session = Depends(depends_db),
            pagination: Pagination = Depends(depends_pagination),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> PagedResponse[SearchObject]:
            handler: EndpointHandler = EndpointHandler(
                db,
                self._search_config,
                pagination,
                query,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PagedResponse[SearchObject],
            summary=f"Search for objects",
            description=None,
            tags=["Search"],
        )

        return router


class MssqlSearchEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "mssql_search"

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

        search_config: SearchConfig = SearchConfig(**resolver_config)

        return MssqlSearchEndpoint(
            path=path,
            search_config=search_config,
        )
