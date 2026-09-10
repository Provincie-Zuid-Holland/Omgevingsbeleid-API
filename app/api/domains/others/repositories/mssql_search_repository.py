from sqlalchemy import TextClause, text
from sqlalchemy.orm import Session

from app.api.domains.others.repositories.search_repository import SearchRepository
from app.api.domains.others.types import ValidSearchConfig
from app.api.utils.pagination import SimplePagination
from app.core.tables.objects import ObjectsTable


class MssqlSearchRepository(SearchRepository):
    def search(
        self,
        query: str,
        session: Session,
        object_types: list[str] | None,
        pagination: SimplePagination,
        search_config: ValidSearchConfig,
    ):
        placeholders = ",".join([f":object_type{i}" for i in range(len(object_types))])
        object_type_filter = f" AND v.Object_Type IN ( {placeholders})"
        stmt = self._get_query(object_type_filter, search_config)

        bindparams_dict = {
            "query": f'"{query}"',
            "offset": pagination.offset,
            "limit": pagination.limit,
        }
        if object_types:
            for i, ot in enumerate(object_types):
                bindparams_dict[f"object_type{i}"] = ot

        stmt = stmt.bindparams(**bindparams_dict)

        results = session.execute(stmt)
        return results

    def _get_query(self, object_type_filter: str, search_config: ValidSearchConfig) -> TextClause:
        stmt = text(
            f"""
                WITH valid_uuids
                AS
                (
                    SELECT
                        *
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
                    ) AS valid_subquery
                    WHERE
                        _RowNumber = 1
                        AND (End_Validity > GETDATE() OR End_Validity IS NULL)
                )

                SELECT
                    v.*,
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
                        SELECT Rank * 1 as Rank, [KEY] from CONTAINSTABLE({ObjectsTable.__table__}, ({", ".join(search_config.searchable_columns_high)}), :query)
                            UNION
                        SELECT Rank * 0.5 as Rank, [KEY] from CONTAINSTABLE({ObjectsTable.__table__}, ({", ".join(search_config.searchable_columns_low)}), :query)
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
