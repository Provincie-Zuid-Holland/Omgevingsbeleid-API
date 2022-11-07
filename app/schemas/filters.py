from enum import Enum
from typing import List, Optional
import csv

from pydantic import BaseModel, Field
from sqlalchemy.orm import Query
from sqlalchemy.sql.expression import and_, or_

from app.core.exceptions import FilterNotAllowed


class Filter(BaseModel):
    key: str
    value: str
    negation: bool = False


class FilterCombiner(Enum):
    AND = 2
    OR = 3


class FilterClause(BaseModel):
    combiner: FilterCombiner
    items: List[Filter]


class Filters(BaseModel):
    clauses: List[FilterClause] = Field(default=[])

    def __init__(self, filter_dict: Optional[dict] = None):
        """
        If dict supplied on instantiation, build filter clauses
        from dict using the AND combiner
        """
        super().__init__()
        self.clauses = []
        if filter_dict:
            self.add_from_dict(FilterCombiner.AND, filter_dict)

    def apply_to_query(self, model, query: Query, alias=None) -> Query:
        """
        Apply the built filter clauses to a given Query input
        """
        allowed_filter_keys = model.get_allowed_filter_keys()

        for clause in self.clauses:
            expressions = []

            for item in clause.items:
                if item.key not in allowed_filter_keys:
                    raise FilterNotAllowed(filter=item.key)

                if alias:
                    column = getattr(alias, item.key)
                else:
                    column = getattr(model, item.key)

                if item.negation:
                    # For NOT filters
                    expressions.append(column != item.value)
                else:
                    expressions.append(column == item.value)

            if expressions:
                if clause.combiner == FilterCombiner.OR:
                    query = query.filter(or_(*expressions))
                else:
                    query = query.filter(and_(*expressions))

        return query

    def add_from_string(self, combiner: FilterCombiner, data: str):
        """
        example:
            "Titel:The Titel,ID:100"
        """
        result_items: List[Filter] = []

        # We are using csv to parse the string as it knows how to parse strings with quotes
        reader = csv.reader([data])
        for item in list(reader)[0]:
            pieces = item.split(":", 1)
            if len(pieces) != 2:
                raise ValueError("Filter does not have a key and a value")
            result_items.append(Filter(key=pieces[0], value=pieces[1]))

        self._append_clause(combiner, result_items)

    def add_from_dict(self, combiner: FilterCombiner, filters: dict):
        """
        Build filter clauses from dictionaries in
        Attribute : Value format.
        """
        result_items: List[Filter] = []

        for key, value in filters.items():
            result_items.append(Filter(key=key, value=value))

        self._append_clause(combiner, result_items)

    def _append_clause(self, combiner: FilterCombiner, items: List):
        clause = FilterClause(combiner=combiner, items=items)
        self.clauses.append(clause)
