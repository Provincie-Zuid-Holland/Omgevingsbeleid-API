from enum import Enum
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import csv

from fastapi import HTTPException


@dataclass
class Filter:
    key: str
    value: str
    negation: bool = False


class FilterCombiner(Enum):
    AND = 2
    OR = 3


@dataclass
class FilterClause:
    combiner: FilterCombiner
    items: List[Filter]


class Filters:
    def __init__(self, filter_dict: Optional[dict] = None):
        self._clauses: List[FilterClause] = []
        if filter_dict:
            self.add_from_dict(FilterCombiner.AND, filter_dict)

    def add_from_string(self, combiner: FilterCombiner, data: str):
        """
        example:
            "Title:The Titel,ID:100"
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

    def add_from_list(self, combiner: FilterCombiner, filters: List[Tuple]):
        result_items: List[Filter] = []

        for key, value in filters:
            result_items.append(Filter(key=key, value=value))

        self._append_clause(combiner, result_items)

    def _append_clause(self, combiner: FilterCombiner, items: List[Filter]):
        clause = FilterClause(combiner=combiner, items=items)
        self._clauses.append(clause)

    def guard_keys(self, allowed_keys: List[str]):
        key_lookup: Dict[str, bool] = {k: True for k in allowed_keys}
        """
        Raises exception if a key is used for filtering which is not in the allowed list
        """
        for clause in self._clauses:
            for filter in clause.items:
                if not filter.key in key_lookup:
                    raise HTTPException(status_code=400, detail="Invalid filter")

    def get_clauses(self) -> List[FilterClause]:
        return self._clauses
