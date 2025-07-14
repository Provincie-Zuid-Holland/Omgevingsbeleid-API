import csv
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, Tuple

from fastapi import HTTPException, status


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
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Filter does not have a key and a value")
            result_items.append(Filter(key=pieces[0], value=pieces[1]))

        self._append_clause(combiner, result_items)

    def add_from_dict(self, combiner: FilterCombiner, filters: dict):
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
        allowed_set = set(allowed_keys)
        for clause in self._clauses:
            for filter in clause.items:
                if not filter.key in allowed_set:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid filter")

    def get_clauses(self) -> List[FilterClause]:
        return self._clauses


@dataclass
class FiltersConverterResult:
    query_part: str
    parameters: List[Any]

    def has_data(self) -> bool:
        return bool(self.parameters)


def convert_filters(filters: Filters):
    query_parts: List[str] = []
    parameters: List[Any] = []

    for clause in filters.get_clauses():
        clause_parts: List[str] = []
        for item in clause.items:
            clause_parts.append(f"{item.key} = ?")
            parameters.append(item.value)
        combiner: str = " OR " if clause.combiner == FilterCombiner.OR else " AND "
        query_parts.append(f"( {combiner.join(clause_parts)} )")

    return FiltersConverterResult(
        query_part=" AND ".join(query_parts),
        parameters=parameters,
    )
