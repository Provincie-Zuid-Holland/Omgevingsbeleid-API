import json
from typing import Annotated, List, Optional, Dict, Set, Sequence, Any

from bs4 import BeautifulSoup
from dependency_injector.wiring import Provide
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import TextClause, Table, bindparam
from sqlalchemy import select, func, text, union_all, literal
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_simple_pagination
from app.api.domains.modules.services.module_objects_to_models_parser import ModuleObjectsToModelsParser
from app.api.domains.others.types import SearchConfig, SearchObject, ValidSearchConfig, SearchRequestDataWithLike
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import PagedResponse, SimplePagination
from app.core.tables.modules import ModuleObjectsTable, ModuleTable
from app.core.tables.objects import ObjectsTable


class EndpointHandler:
    def __init__(
        self,
        session: Session,
        module_objects_to_models_parser: ModuleObjectsToModelsParser,
        model_map: Dict[str, str],
        search_config: SearchConfig,
        pagination: SimplePagination,
        query: str,
        object_types: Optional[List[str]] = None,
        as_like: bool = False,
    ):
        self._session: Session = session
        self._module_objects_to_models_parser: ModuleObjectsToModelsParser = module_objects_to_models_parser
        self._model_map: Dict[str, str] = model_map
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
        object_type_filter = f" AND v.Object_Type IN ({placeholders})"

        bindparams_dict: Dict[str, Any] = {
            "offset": self._pagination.offset,
            "limit": self._pagination.limit,
        }

        objects_field_set: Set[str] = set([c.name for c in ObjectsTable.__table__.columns])
        module_objects_field_set: Set[str] = set([c.name for c in ModuleObjectsTable.__table__.columns])
        fields: Set[str] = objects_field_set.intersection(module_objects_field_set)

        if self._as_like:
            stmt = self._get_like_query(object_type_filter, fields)
            bindparams_dict["query"] = f"%{self._query}%"
        else:
            stmt = self._get_query(object_type_filter, fields)
            bindparams_dict["query"] = f'"{self._query}"'

        if self._object_types:
            bindparams_dict["object_types"] = self._object_types

        results = self._session.execute(stmt, bindparams_dict)
        search_objects: List[SearchObject] = []
        total_count: int = 0

        for row in results:
            row = row._asdict()
            parsed_model: BaseModel = self._module_objects_to_models_parser.parse_from_dict(
                row["Object_Type"],
                row,
                self._model_map,
            )

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
                Model=parsed_model,
            )
            search_objects.append(search_object)
            total_count = row["_Total_Count"]

        return PagedResponse[SearchObject](
            total=total_count,
            offset=self._pagination.offset,
            limit=self._pagination.limit,
            results=search_objects,
        )

    def _get_query(self, object_types: Optional[List[str]], fields: Set[str]):
        objects = ObjectsTable.__table__
        module_objects = ModuleObjectsTable.__table__
        modules = ModuleTable.__table__

        row_number = func.row_number().over(
            partition_by=objects.c.Code,
            order_by=objects.c.Modified_Date.desc(),
        )

        valid_objects = (
            select(
                literal(0).label("Module_ID"),
                *[objects.c[f] for f in fields],
                row_number.label("_rn"),
            )
            .where(ObjectsTable.__table__.c.Start_Validity <= func.now())
            .subquery()
        )

        valid_objects_cte = select(
            valid_objects.c.Module_ID,
            *[valid_objects.c[f] for f in fields],
        ).where(
            valid_objects.c._rn == 1,
            (valid_objects.c.End_Validity > func.now()) | (valid_objects.c.End_Validity.is_(None)),
        )

        row_number_mo = func.row_number().over(
            partition_by=module_objects.c.Code, order_by=module_objects.c.Modified_Date.desc()
        )

        module_objects_sq = (
            select(
                module_objects,
                row_number_mo.label("_rn"),
            )
            .join(modules, module_objects.c.Module_ID == modules.c.Module_ID)
            .where(modules.c.Closed.is_(False))
            .subquery()
        )

        valid_module_objects_cte = select(
            module_objects_sq.c.Module_ID,
            *[module_objects_sq.c[f] for f in fields],
        ).where(module_objects_sq.c._rn == 1)

        valid_uuids = union_all(
            valid_objects_cte,
            valid_module_objects_cte,
        ).cte("valid_uuids")

        def rank_expr(table: Table, columns: Sequence[str], weight: float):
            vector = func.to_tsvector(
                "simple",
                func.concat_ws(" ", *[table.c[c] for c in columns]),
            )
            query = func.plainto_tsquery("simple", self._query)
            return func.ts_rank(vector, query) * weight

        rank_objects = select(
            objects.c.UUID.label("uuid"),
            rank_expr(objects, self._search_config.searchable_columns_high, 1).label("rank"),
        ).where(
            func.to_tsvector(
                "simple",
                func.concat_ws(" ", *[objects.c[c] for c in self._search_config.searchable_columns_high]),
            ).op("@@")(func.plainto_tsquery("simple", self._query))
        )

        rank_objects_low = select(
            objects.c.UUID.label("uuid"),
            rank_expr(objects, self._search_config.searchable_columns_low, 0.5).label("rank"),
        )

        rank_module_objects = select(
            module_objects.c.UUID.label("uuid"),
            rank_expr(module_objects, self._search_config.searchable_columns_high, 1).label("rank"),
        )

        rank_module_objects_low = select(
            module_objects.c.UUID.label("uuid"),
            rank_expr(module_objects, self._search_config.searchable_columns_low, 0.5).label("rank"),
        )

        rank_union = union_all(
            rank_objects,
            rank_objects_low,
            rank_module_objects,
            rank_module_objects_low,
        ).subquery()

        ranked = (
            select(
                rank_union.c.uuid,
                func.sum(rank_union.c.rank).label("WeightedRank"),
            )
            .group_by(rank_union.c.uuid)
            .subquery()
        )

        stmt = (
            select(
                valid_uuids.c.Module_ID,
                *[valid_uuids.c[f] for f in fields],
                ranked.c.WeightedRank.label("_Rank"),
                func.count().over().label("_Total_Count"),
            )
            .join(ranked, ranked.c.uuid == valid_uuids.c.UUID)
            .order_by(ranked.c.WeightedRank.desc())
            .offset(self._pagination.offset)
            .limit(self._pagination.limit)
        )

        if not object_types:
            return stmt

        return stmt.where(valid_uuids.c.Object_Type.in_(bindparam("object_types", expanding=True)))

    def _get_query_old(self, object_type_filter: str, fields: Set[str]) -> TextClause:
        stmt = text(
            f"""
                WITH valid_uuids
                AS
                (
                    SELECT
                        0 AS Module_ID,
                        {", ".join(fields)}
                    FROM (
                        SELECT
                            *,
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
                    ) AS valid_objects
                    WHERE
                        _RowNumber = 1
                        AND (End_Validity > GETDATE() OR End_Validity IS NULL)
                    
                    UNION

                    SELECT
                        Module_ID,
                        {", ".join(fields)}
                    FROM (
                        SELECT
                            mo.*,
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
                    ) AS module_objects
                    WHERE
                        _RowNumber = 1
                )

                SELECT
                    v.Module_ID,
                    {", ".join(f"v.{f}" for f in fields)},
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

    def _get_like_query(self, object_type_filter: str, fields: Set[str]) -> TextClause:
        stmt = text(
            f"""
                WITH valid_uuids
                AS
                (
                    SELECT
                        0 AS Module_ID,
                        {", ".join(fields)}
                    FROM (
                        SELECT
                            *,
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
                    ) AS valid_objects
                    WHERE
                        _RowNumber = 1
                        AND (End_Validity > GETDATE() OR End_Validity IS NULL)
                    
                    UNION

                    SELECT
                        Module_ID,
                        {", ".join(fields)}
                    FROM (
                        SELECT
                            mo.*,
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
                    ) AS module_objects
                    WHERE
                        _RowNumber = 1
                )

                SELECT
                    v.Module_ID,
                    {", ".join(f"v.{f}" for f in fields)},
                    1 AS _Rank,
                    COUNT(*) OVER() AS _Total_Count
                FROM valid_uuids AS v
                WHERE
                    (
                        Title LIKE :query
                        OR Description LIKE :query
                    )
                    {object_type_filter}
                ORDER BY v.Module_ID DESC
                OFFSET
                    :offset ROWS
                FETCH
                    NEXT :limit ROWS ONLY
            """
        )
        return stmt


class PostgresqlSearchEndpointContext(BaseEndpointContext):
    search_config: ValidSearchConfig
    model_map: Dict[str, str]


def get_postgresql_search_endpoint(
    query: str,
    object_in: SearchRequestDataWithLike,
    session: Annotated[Session, Depends(depends_db_session)],
    pagination: Annotated[SimplePagination, Depends(depends_simple_pagination)],
    context: Annotated[PostgresqlSearchEndpointContext, Depends()],
    module_objects_to_models_parser: Annotated[
        ModuleObjectsToModelsParser, Depends(Provide[ApiContainer.module_objects_to_models_parser])
    ],
) -> PagedResponse[SearchObject]:
    handler: EndpointHandler = EndpointHandler(
        session,
        module_objects_to_models_parser,
        context.model_map,
        context.search_config,
        pagination,
        query,
        object_in.Object_Types,
        object_in.Like,
    )
    results: PagedResponse[SearchObject] = handler.handle()
    return results
