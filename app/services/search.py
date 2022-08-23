from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.orm import Query, Session, Session, aliased
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.expression import func, label, or_

from app import models
from app.core.exceptions import SearchException
from app.db.base_class import Base
from app.db.session import SessionLocal
from app.util.legacy_helpers import SearchFields

ModelType = TypeVar("ModelType", bound=Base)


class SearchService:
    """
    Service providing text search on generic models
    for per-model configured search fields
    """
    SEARCHABLE_MODELS: List[ModelType] = [
           models.Ambitie,
           models.Beleidskeuze
    ]

    def __init__(self):
        self.db: Session = SessionLocal()
        self.searchable_models: List[ModelType] = [
           models.Ambitie,
           models.Beleidskeuze
        ]

    def search(self, model: Type[ModelType], query: str) -> List[ModelType]:
        """
        Search model for a given search query.
        Builds search query + execute

        Returns:
            List: results listing found models
        """
        return self.build_search_query(model, query).all()

    def search_all_optimized(self, search_query: str):
        """
        Execute search function for all models defined as searchable, and
        aggregate its search results ordered by rank.
        """
        agg_query = None

        for entity in self.SEARCHABLE_MODELS:
            sql_query = self.build_search_query(model=entity, query=search_query)
            if agg_query is None:
                agg_query: Query = sql_query
            else:
                agg_query: Query = agg_query.union(sql_query).subquery("inner")

        results = agg_query.all() 

        return results

    def search_all(self, search_query: str):
        """
        Execute search function for all models defined as searchable, and
        aggregate its search results ordered by rank.
        """
        aggregated_results = list()
        for entity in self.SEARCHABLE_MODELS:
            search_results = self.search(model=entity, query=search_query)
            if search_results:
                aggregated_results.extend(search_results)

        return aggregated_results

    def build_search_query(self, model: Type[ModelType], query: str) -> Query:
        """
        Search model for a given search query.

        Args:
            model (Base): SQLalchemy model entity
            query (str): the search query

        Returns:
            Query: The query object for search execution
        """
        #title_column_search = [searchable_columns.title.ilike(f"%{crit}%") for crit in search_criteria]
        #description_column_search = [model.Omschrijving.ilike(f"%{crit}%") for crit in search_criteria]
        search_criteria = query.split(" ")
        title_column_search, description_column_search = self._build_search_clauses(
               model=model, search_criteria=search_criteria)

        # Build subquery for ranked search results
        rank: ColumnElement = func.row_number().over(order_by=model.Modified_Date.desc())

        title_search_query: Query = self.db.query(model) \
                .add_column(label("Search_Rank", rank)) \
                .filter(or_(*title_column_search))

        description_search_query: Query = self.db.query(model) \
                .add_column(label("Search_Rank", rank+1000)) \
                .filter(or_(*description_column_search))

        search_query: Query = title_search_query.union(description_search_query).subquery('inner')

        alias: AliasedClass = aliased(
                element=model, alias=search_query, name="inner")

        # Fetch results
        search_query: Query = self.db.query(alias) \
                .add_columns(search_query.c.Search_Rank) \
                .order_by(search_query.c.Search_Rank) \

        return search_query

    def _build_search_clauses(self, model: Type[ModelType], search_criteria: List[str]):
        """
        Build sql filter clauses for every search_field <-> search word
        combination.
        """
        searchable_columns: SearchFields = model.get_search_fields()

        title_column = list()
        description_column = list()
        
        for crit in search_criteria:
            title_column.append(searchable_columns.title.ilike(f"%{crit}%"))
            for column in searchable_columns.description:
                description_column.append(column.ilike(f"%{crit}%"))

        return title_column, description_column


search_service = SearchService()
