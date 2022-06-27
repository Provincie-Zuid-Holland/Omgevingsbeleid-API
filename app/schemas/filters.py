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
            pieces = item.split(':', 1)
            if len(pieces) != 2:
                raise ValueError('Filter does not have a key and a value')
            result_items.append(Filter(key=pieces[0], value=pieces[1]))

        self.clauses.append(FilterClause(combiner=combiner, items=result_items))
