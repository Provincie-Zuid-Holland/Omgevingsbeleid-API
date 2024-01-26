import json
from typing import List, Optional

from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends
from sqlalchemy import TextClause, text
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.db import ObjectsTable
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.mssql_search.models import SearchConfig, SearchObject, SearchRequestData
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        search_config: SearchConfig,
        pagination: SimplePagination,
        query: str,
        object_types: Optional[List[str]] = None,
        as_like: bool = False,
    ):
        self._db: Session = db
        self._search_config: SearchConfig = search_config
        self._pagination: SimplePagination = pagination
        self._query: str = query
        self._object_types: Optional[List[str]] = object_types
        self._as_like: bool = as_like

    def handle(self) -> PagedResponse[SearchObject]:
        if not len(self._query):
            raise ValueError("Missing search query")
        if "\\" in json.dumps(self._query):
            raise ValueError("Invalid search characters")
        if self._pagination.limit > 50:
            raise ValueError("Pagination limit is too high")
        if self._object_types:
            for object_type in self._object_types:
                if object_type not in self._search_config.allowed_object_types:
                    raise ValueError(f"Allowed Object_Types are: {self._search_config.allowed_object_types}")
        else:
            # default to all
            self._object_types = self._search_config.allowed_object_types

        placeholders = ",".join([f":object_type{i}" for i in range(len(self._object_types))])
        object_type_filter = f" AND v.Object_Type IN ( {placeholders})"
        if self._as_like:
            stmt = self._get_like_query(object_type_filter)
        else:
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
        search_objects: List[SearchObject] = []
        total_count: int = 0

        for row in results:
            row = row._asdict()

            description: str = ""
            if row["Description"] and isinstance(row["Description"], str):
                soup = BeautifulSoup(row["Description"], "html.parser")
                description = soup.get_text()

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
            offset=self._pagination.offset,
            limit=self._pagination.limit,
            results=search_objects,
        )

    def _get_query(self, object_type_filter) -> TextClause:
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

    def _get_like_query(self, object_type_filter) -> TextClause:
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
                    1 AS _Rank,
                    COUNT(*) OVER() AS _Total_Count
                FROM valid_uuids AS v
                WHERE
                    (
                            Title LIKE '%:query%'
                        OR  Description LIKE '%:query%'
                    )
                    {object_type_filter}
                OFFSET
                    :offset ROWS
                FETCH
                    NEXT :limit ROWS ONLY
            """
        )
        return stmt


class MssqlSearchEndpoint(Endpoint):
    def __init__(self, path: str, search_config: SearchConfig):
        self._path: str = path
        self._search_config: SearchConfig = search_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            query: str,
            object_in: SearchRequestData,
            db: Session = Depends(depends_db),
            pagination: SimplePagination = Depends(depends_simple_pagination),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> PagedResponse[SearchObject]:
            handler: EndpointHandler = EndpointHandler(
                db, self._search_config, pagination, query, object_in.Object_Types, object_in.Like
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
