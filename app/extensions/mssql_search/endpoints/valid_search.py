from typing import List
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator
from sqlalchemy import text
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
        pagination: Pagination,
        query: str,
    ):
        self._db: Session = db
        self._pagination: Pagination = pagination
        self._query: str = query

    def handle(self) -> SearchResponse:
        if not len(self._query):
            raise ValueError("Missing search query")

        stmt = text(
            f"""
                WITH valid_uuids (UUID, Object_Type, Object_ID, Title, Description)
                AS
                (
                    SELECT
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
                )

                SELECT
                    v.UUID,
                    v.Object_Type,
                    v.Object_ID,
                    v.Title,
                    v.Description,
                    CAST(FLOOR(s.WeightedRank) AS INT) AS _Rank
                FROM valid_uuids AS v
                INNER JOIN
                (
                    SELECT
                        [KEY],
                        SUM(Rank) as WeightedRank
                    FROM
                    (
                        SELECT Rank * 1 as Rank, [KEY] from CONTAINSTABLE({ObjectsTable.__table__}, (Title), :query)
                            UNION
                        SELECT Rank * 0.5 as Rank, [KEY] from CONTAINSTABLE({ObjectsTable.__table__}, (Description), :query)
                    ) AS x
                    GROUP BY [KEY]
                ) AS s ON s.[KEY] = v.UUID
                ORDER BY
                    s.WeightedRank DESC
                OFFSET
                    0 ROWS 
                FETCH
                    NEXT 10 ROWS ONLY
            """
        )

        # stmt = self._search_stmt()
        # table_rows = self._db.execute(stmt).all()
        # search_objects: List[SearchObject] = [
        #     SearchObject.parse_obj(r._asdict()) for r in table_rows
        # ]

        return SearchResponse(
            Objects=[],
        )


class MssqlValidSearchEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            query: str,
            db: Session = Depends(depends_db),
            pagination: Pagination = Depends(depends_pagination),
        ) -> SearchResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                pagination,
                query,
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
