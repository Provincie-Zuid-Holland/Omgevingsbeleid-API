from typing import Any, List

from sqlalchemy.orm import Query, Session, Session, aliased
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.expression import func, label, or_

from app.crud.base import CRUDBase
from app.util.legacy_helpers import RankedSearchObject, SearchFields


RANK_WEIGHT = 1
RANK_WEIGHT_HEAVY = 100


class SearchService:
    """
    Service providing text search on generic models
    for per-model configured search fields
    """

    def __init__(self, db: Session, search_cruds: List[CRUDBase]):
        self.db = db
        self.search_cruds = search_cruds

    def search(
        self, crud: CRUDBase, search_criteria: List[str]
    ) -> List[RankedSearchObject]:
        """
        Search model for a given search query.
        Builds search query + execute

        Returns:
            List: results listing found models
        """

        query_results = self.build_search_query(
            crud=crud, search_criteria=search_criteria
        ).all()

        ranked_items = [
            RankedSearchObject(object=item[0], rank=item[1]) for item in query_results
        ]
        return ranked_items

    # TODO: self.search currently inefficient
    def search_all_optimized(self, search_criteria: List[str]):
        """
        Execute search function for all models defined as searchable, and
        aggregate its search results ordered by rank.
        """
        raise NotImplementedError()

    def search_all(self, search_criteria: List[str]) -> List[RankedSearchObject]:
        """
        Execute search function for all models defined as searchable, and
        aggregate its search results ordered by rank.
        """
        aggregated_results = list()
        for crud in self.search_cruds:
            search_results = self.search(crud=crud, search_criteria=search_criteria)
            if search_results:
                aggregated_results.extend(search_results)

        sorted_results = sorted(aggregated_results, key=lambda x: x[1])
        return sorted_results

    def build_search_query(self, crud: CRUDBase, search_criteria: List[str]) -> Query:
        """
        Search model for a given search query.

        Args:
            model (Base): SQLalchemy model entity
            query (str): the search query

        Returns:
            Query: The query object for search execution
        """
        valid_sub_query = crud._build_valid_view_filter(as_subquery=True)
        base_alias: AliasedClass = aliased(element=crud.model, alias=valid_sub_query)

        # Search clauses
        title_column_search, description_column_search = self._build_search_clauses(
            model=crud.model, search_criteria=search_criteria, aliased_model=base_alias
        )

        # Rank criteria
        modified_date = base_alias.__getattr__(crud.model.Modified_Date.key)
        rank = func.row_number().over(order_by=modified_date.desc())

        # Search queries
        normal_weight_query: Query = (
            self.db.query(base_alias)
            .add_column(label("Search_Rank", rank))
            .filter(or_(*title_column_search))
        )

        heavy_weight_query: Query = (
            self.db.query(base_alias)
            .add_column(label("Search_Rank", (rank + RANK_WEIGHT_HEAVY)))
            .filter(or_(*description_column_search))
        )

        combined_query: Query = Query.union(normal_weight_query, heavy_weight_query)

        return combined_query.order_by(rank)

    def _build_search_clauses(
        self, model: Any, search_criteria: List[str], aliased_model: AliasedClass
    ):
        """
        Build sql filter clauses for every search_field <-> search word
        combination.
        """
        searchable_columns: SearchFields = model.get_search_fields()

        title_column = list()
        description_column = list()

        for crit in search_criteria:
            # Title search
            title_field = searchable_columns.title
            if aliased_model is not None:
                title_field = getattr(aliased_model, searchable_columns.title.key)

            title_column.append(title_field.ilike(f"%{crit}%"))

            # Description search
            for column in searchable_columns.description:
                description_field = column
                if aliased_model is not None:
                    description_field = getattr(aliased_model, column.key)

                description_column.append(description_field.ilike(f"%{crit}%"))

        return title_column, description_column
