from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.domains.others.repositories.search_repository import SearchRepository
from app.api.domains.others.types import ValidSearchConfig
from app.api.utils.pagination import SimplePagination
from app.core.tables.objects import ObjectsTable


class PostgresqlSearchRepository(SearchRepository):
    def search(
        self,
        query: str,
        session: Session,
        object_types: list[str] | None,
        pagination: SimplePagination,
        search_config: ValidSearchConfig,
    ):
        table = ObjectsTable.__table__

        row_number = (
            func.row_number().over(partition_by=table.c.Code, order_by=table.c.Modified_Date.desc()).label("_RowNumber")
        )

        valid_subquery = (
            select(table, row_number).where(table.c.Start_Validity <= func.now()).subquery("valid_subquery")
        )

        valid_uuids = (
            select(valid_subquery)
            .where(
                valid_subquery.c["_RowNumber"] == 1,
                or_(
                    valid_subquery.c.End_Validity > func.now(),
                    valid_subquery.c.End_Validity.is_(None),
                ),
            )
            .cte("valid_uuids")
        )

        def tsvector_for(columns: list[str]):
            parts = [func.coalesce(table.c[c], "") for c in columns]
            concat = parts[0]
            for p in parts[1:]:
                concat = concat + " " + p
            return func.to_tsvector("simple", concat)

        tsquery = func.plainto_tsquery("simple", query)

        weighted_rank = (
            func.ts_rank_cd(tsvector_for(search_config.searchable_columns_high), tsquery) * 1.0
            + func.ts_rank_cd(tsvector_for(search_config.searchable_columns_low), tsquery) * 0.5
        )

        ranked = select(table.c.UUID, weighted_rank.label("_weighted_rank")).cte("ranked")

        stmt = (
            select(
                valid_uuids,
                ranked.c._weighted_rank.label("_Rank"),
                func.count().over().label("_Total_Count"),
            )
            .select_from(valid_uuids.join(ranked, ranked.c.UUID == valid_uuids.c.UUID))
            .where(ranked.c._weighted_rank > 0)
            .order_by(ranked.c._weighted_rank.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )

        if object_types:
            stmt = stmt.where(valid_uuids.c.Object_Type.in_(object_types))

        return session.execute(stmt)
