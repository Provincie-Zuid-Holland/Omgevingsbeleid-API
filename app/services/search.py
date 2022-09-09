from os import wait
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeMeta, Query, Session, Session, aliased
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.expression import and_, func, label, or_

from app import models
from app.core.exceptions import SearchException
from app.crud.base import CRUDBase
from app.db.base_class import Base
from app.db.session import SessionLocal
from app.util.legacy_helpers import RankedSearchObject, SearchFields
from app.util.word_filter import get_filtered_search_criteria

ModelType = TypeVar("ModelType", bound=Base)


class SearchService:
    """
    Service providing text search on generic models
    for per-model configured search fields
    """

    SEARCHABLE_MODELS: List[Any] = [
        models.Ambitie,
        models.Beleidskeuze,
        models.Belang,
        models.Beleidsdoel,
        models.Beleidsprestatie,
        models.Beleidsregel,
        models.Maatregel,
        models.Thema,
    ]
    RANK_WEIGHT = 1
    RANK_WEIGHT_HEAVY = 100

    def __init__(self):
        self.db: Session = SessionLocal()

    def search(
        self, model: Any, query: str
    ) -> List[RankedSearchObject]:
        """
        Search model for a given search query.
        Builds search query + execute

        Returns:
            List: results listing found models
        """
        query_results = self.build_search_query(model=model, search_query=query).all()
        ranked_items = [RankedSearchObject(object=item[0], rank=item[1]) for item in query_results]
        return ranked_items

    def search_all_optimized(self, search_query: str):
        """
        Execute search function for all models defined as searchable, and
        aggregate its search results ordered by rank.
        """
        #TODO: self.search currently inefficient
        raise NotImplementedError() 

    def search_all(self, search_query: str) -> List[RankedSearchObject]:
        """
        Execute search function for all models defined as searchable, and
        aggregate its search results ordered by rank.
        """
        aggregated_results = list()
        for entity in self.SEARCHABLE_MODELS:
            search_results = self.search(model=entity, query=search_query)
            if search_results:
                aggregated_results.extend(search_results)

        sorted_results = sorted(aggregated_results, key=lambda x: x[1])
        return sorted_results

    def build_search_query(
            self, model: Any, search_query: str
    ) -> Query:
        """
        Search model for a given search query.

        Args:
            model (Base): SQLalchemy model entity
            query (str): the search query

        Returns:
            Query: The query object for search execution
        """
        crud_service = CRUDBase(model)
        valid_sub_query = crud_service._build_valid_view_filter(as_subquery=True)
        base_alias: AliasedClass = aliased(element=model, alias=valid_sub_query)
        
        # Search clauses
        search_criteria = get_filtered_search_criteria(search_query)
        title_column_search, description_column_search = self._build_search_clauses(
            model=model, search_criteria=search_criteria, aliased_model=base_alias
        )

        # Rank criteria
        modified_date = base_alias.__getattr__(model.Modified_Date.key)
        rank = func.row_number().over(order_by=modified_date.desc())

        # Search queries
        normal_weight_query: Query = (
            self.db.query(base_alias)
            .add_column(label("Search_Rank", rank))
            .filter(or_(*title_column_search))
        )

        heavy_weight_query: Query = (
            self.db.query(base_alias)
            .add_column(label("Search_Rank", (rank + self.RANK_WEIGHT_HEAVY)))
            .filter(or_(*description_column_search))
        )

        combined_query: Query = Query.union(normal_weight_query, heavy_weight_query)

        return combined_query.order_by(rank)


    def _build_search_clauses(self, model: Any, search_criteria: List[str], aliased_model: AliasedClass = None):
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
                title_field = aliased_model.__getattr__(searchable_columns.title.key)

            title_column.append(title_field.ilike(f"%{crit}%"))

            # Description search
            for column in searchable_columns.description:
                description_field = column
                if aliased_model is not None:
                    description_field = aliased_model.__getattr__(column.key)

                description_column.append(description_field.ilike(f"%{crit}%"))

        return title_column, description_column


search_service = SearchService()
