from enum import Enum
from typing import List
import csv

from pydantic import BaseModel, Field


class Filter(BaseModel):
    key: str
    value: str


class FilterCombiner(Enum):
    AND = 2
    OR = 3


class FilterClause(BaseModel):
    combiner: FilterCombiner
    items: List[Filter]


class Filters(BaseModel):
    clauses: List[FilterClause] = Field(default=[])

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
        result_items: List[Filter] = []

        for key, value in filters.items():
            result_items.append(Filter(key=key, value=value))

        self._append_clause(combiner, result_items)

    def _append_clause(self, combiner: FilterCombiner, items: List):
        clause = FilterClause(combiner=combiner, items=items)
        self.clauses.append(clause)
