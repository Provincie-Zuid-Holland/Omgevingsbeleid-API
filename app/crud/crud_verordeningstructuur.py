from typing import Any, List, Optional, Tuple

from sqlalchemy.orm import Query, aliased
from sqlalchemy.sql import func, label
from app.crud.base import CRUDBase
from app.db.base_class import NULL_UUID
from app.models import Verordeningstructuur
from app.schemas.filters import Filters
from app.schemas.verordeningstructuur import (
    VerordeningstructuurUpdate,
    VerordeningstructuurCreate,
)


class CRUDVerordeningstructuur(
    CRUDBase[
        Verordeningstructuur, VerordeningstructuurCreate, VerordeningstructuurUpdate
    ]
):
    def valid(
        self,
        ID: Optional[int] = None,
        offset: int = 0,
        limit: int = -1,
        filters: Optional[Filters] = None,
    ) -> List[Verordeningstructuur]:
        return self.actual_view(ID, offset, limit, filters)

    def _build_latest_view_filter(
        self, all: bool = None, filters: Optional[Filters] = None
    ) -> Query:
        row_number = self._add_rownumber_latest_id()
        sub_query = Query([Verordeningstructuur, row_number]).subquery("inner")
        model_alias = aliased(
            element=Verordeningstructuur,
            alias=sub_query,
            name="inner",
            adapt_on_names=True,
        )
        query = (
            Query(model_alias)
            .filter(sub_query.c.RowNumber == 1)
            .filter(model_alias.UUID != NULL_UUID)
        )
        query = self._build_filtered_query(
            query=query, model=model_alias, filters=filters
        )
        return query.order_by(model_alias.ID.desc())

    def actual_view(
        self,
        ID: Optional[int] = None,
        offset: int = 0,
        limit: int = -1,
        filters: Optional[Filters] = None,
    ) -> List[Verordeningstructuur]:
        query, alias = self._build_actual_view_query(ID)
        if filters:
            query = filters.apply_to_query(model=self.model, query=query, alias=alias)
        else:
            query = self._build_filtered_query(query=query, filters=filters)

        ordered = query.order_by(alias.ID.desc())
        query = ordered.offset(offset)

        if limit != -1:
            query = query.limit(limit)

        query.session = self.db
        return query.all()

    def _build_actual_view_query(self, ID: Optional[int] = None) -> Tuple[Query, Any]:
        sub_query = self._build_actual_inner_query().subquery("inner")
        inner_alias: Verordeningstructuur = aliased(
            element=Verordeningstructuur, alias=sub_query, name="inner"
        )
        last_modified_id_filter = sub_query.c.get("RowNumber") == 1
        query = Query(inner_alias).filter(last_modified_id_filter)

        if ID is not None:
            query = query.filter(inner_alias.ID == ID)

        return query, inner_alias

    def _build_actual_inner_query(self) -> Query:
        partition = func.row_number().over(
            partition_by=Verordeningstructuur.ID,
            order_by=Verordeningstructuur.Modified_Date.desc(),
        )
        row_number = label("RowNumber", partition)
        query = Query([Verordeningstructuur, row_number]).filter(
            Verordeningstructuur.UUID != NULL_UUID
        )
        return query
