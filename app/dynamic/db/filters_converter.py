from typing import List, Any
from dataclasses import dataclass

from app.dynamic.utils.filters import Filters, FilterCombiner


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
        combiner: str = _resolve_combiner(clause.combiner)
        query_parts.append(f"( {combiner.join(clause_parts)} )")

    result: FiltersConverterResult = FiltersConverterResult(
        query_part=" AND ".join(query_parts),
        parameters=parameters,
    )

    return result


def _resolve_combiner(combiner: FilterCombiner) -> str:
    if combiner == FilterCombiner.OR:
        return " OR "

    return " AND "
