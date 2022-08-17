from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.db.session import SessionLocal

ModelType = TypeVar("ModelType", bound=BaseModel)


class SearchService:
    def __init__(self):
        self.db: Session = SessionLocal

    def search(self, model: Type[ModelType], query: str):
        """
        Search for a given query.

        Args:
            query (str): the search query

        Returns:
            List: The object matching the query
        """

        input = "Overstromingen parent seller"
        
        # Search prep
        search_criteria = input.split(" ")
        searchable_columns = models.Ambitie.get_search_fields()

        title_column_search = [models.Ambitie("Titel").ilike(f"%{crit}%") for crit in search_criteria]
        description_column_search = [models.Ambitie.Omschrijving.ilike(f"%{crit}%") for crit in search_criteria]

        # Build subquery for ranked search results
        rank: ColumnElement = func.row_number().over(order_by=models.Ambitie.Modified_Date.desc())
        
        title_search_query: Query = db.query(models.Ambitie, label("Search_Rank", rank)) \
            .filter(or_(*title_column_search))

        description_search_query: Query = db.query(models.Ambitie, label("Search_Rank", (1000+rank))) \
           .filter(or_(*description_column_search))

        search_query: Query = title_search_query.union(description_search_query).subquery('inner')
        
        alias: AliasedClass = aliased(
            element=models.Ambitie, alias=search_query, name="inner"
        )

        # Fetch results
        results: Query = db.query(alias) \
                .add_columns(search_query.c.Search_Rank) \
                .order_by(search_query.c.Search_Rank) \
                .all()

search_service = SearchService()
