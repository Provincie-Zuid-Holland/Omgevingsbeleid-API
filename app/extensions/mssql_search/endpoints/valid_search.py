import json
import uuid
from typing import List, Optional

from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator
from sqlalchemy import TextClause, text
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.dependencies import depends_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, Pagination
from app.extensions.mssql_search.models import SearchRequestData, ValidSearchConfig, ValidSearchObject


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        search_config: ValidSearchConfig,
        pagination: Pagination,
        query: str,
        object_types: Optional[List[str]] = None,
    ):
        self._db: Session = db
        self._search_config: ValidSearchConfig = search_config
        self._pagination: Pagination = pagination
        self._query: str = query
        self._object_types: Optional[List[str]] = object_types

    def handle(self) -> PagedResponse[ValidSearchObject]:
        if not len(self._query):
            raise ValueError("Missing search query")
        if "\\" in json.dumps(self._query):
            raise ValueError("Invalid search characters")
        if self._pagination.limit > 50:
            raise ValueError("Pagination limit is too high")
        if self._pagination.limit < 1:
            raise ValueError("Pagination limit is too low")
        if self._object_types:
            for object_type in self._object_types:
                if object_type not in self._search_config.allowed_object_types:
                    raise ValueError(f"Allowed Object_Types are: {self._search_config.allowed_object_types}")
        else:
            # default to all
            self._object_types = self._search_config.allowed_object_types

        placeholders = ",".join([f":object_type{i}" for i in range(len(self._object_types))])
        object_type_filter = f" AND v.Object_Type IN ( {placeholders})"
        stmt = self._get_query(object_type_filter)

        bindparams_dict = {
            "query": f'"{self._query}"',
            "offset": self._pagination.offset,
            "limit": self._pagination.limit,
        }
        # fill object type placeholders
        if self._object_types:
            for i, ot in enumerate(self._object_types):
                bindparams_dict[f"object_type{i}"] = ot

        stmt = stmt.bindparams(**bindparams_dict)

        results = self._db.execute(stmt)
        search_objects: List[ValidSearchObject] = []
        total_count: int = 0

        for row in results:
            row = row._asdict()

            description: str = ""
            if row["Description"] and isinstance(row["Description"], str):
                soup = BeautifulSoup(row["Description"], "html.parser")
                description = soup.get_text()

            search_object: ValidSearchObject = ValidSearchObject(
                UUID=row["UUID"],
                Object_Type=row["Object_Type"],
                Object_ID=row["Object_ID"],
                Title=row["Title"],
                Description=description,
                Score=row["_Rank"],
            )
            search_objects.append(search_object)
            total_count = row["_Total_Count"]

        return PagedResponse[ValidSearchObject](
            total=total_count,
            offset=self._pagination.offset,
            limit=self._pagination.limit,
            results=search_objects,
        )

    def _get_query(self, object_type_filter) -> TextClause:
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
                    ) AS x
                    GROUP BY [KEY]
                ) AS s ON s.[KEY] = v.UUID
                WHERE 1=1 {object_type_filter}
                ORDER BY
                    s.WeightedRank DESC
                OFFSET
                    :offset ROWS 
                FETCH
                    NEXT :limit ROWS ONLY
            """
        )
        return stmt


class MssqlValidSearchEndpoint(Endpoint):
    def __init__(self, path: str, search_config: ValidSearchConfig):
        self._path: str = path
        self._search_config: ValidSearchConfig = search_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            query: str,
            object_in: SearchRequestData,
            db: Session = Depends(depends_db),
            pagination: Pagination = Depends(depends_pagination),
        ) -> PagedResponse[ValidSearchObject]:
            handler: EndpointHandler = EndpointHandler(
                db, self._search_config, pagination, query, object_in.Object_Types
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PagedResponse[ValidSearchObject],
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

        search_config: ValidSearchConfig = ValidSearchConfig(**resolver_config)

        return MssqlValidSearchEndpoint(
            path=path,
            search_config=search_config,
        )
