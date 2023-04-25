import pytest
from fastapi import HTTPException
from app.dynamic.utils.filters import Filter, FilterCombiner, FilterClause, Filters
from app.dynamic.db.filters_converter import (
    FiltersConverterResult,
    convert_filters,
)


class TestFiltering:
    """
    Sanity test basic filter clause and SQL converter.
    """

    def test_string_to_filter(self):
        filters = Filters()
        filters.add_from_string(FilterCombiner.AND, "Title:The Title,ID:100")

        expected_clause = FilterClause(
            combiner=FilterCombiner.AND,
            items=[
                Filter(key="Title", value="The Title"),
                Filter(key="ID", value="100"),
            ],
        )
        assert len(filters.get_clauses()) == 1
        assert filters.get_clauses()[0] == expected_clause

    def test_invalid_input(self):
        filters = Filters()
        with pytest.raises(ValueError, match="Filter does not have a key and a value"):
            filters.add_from_string(FilterCombiner.AND, "Title:The Title,ID")

    def test_not_allowed_key(self):
        filters = Filters()
        filters.add_from_string(FilterCombiner.AND, "Title:The Title,ID:100")

        with pytest.raises(HTTPException):
            filters.guard_keys(["ID"])

    def test_dict_as_filter_input(self):
        filters = Filters()
        filter_dict = {"Title": "The Title", "ID": "100"}
        filters.add_from_dict(FilterCombiner.AND, filter_dict)

        expected_clause = FilterClause(
            combiner=FilterCombiner.AND,
            items=[
                Filter(key="Title", value="The Title"),
                Filter(key="ID", value="100"),
            ],
        )
        assert len(filters.get_clauses()) == 1
        assert filters.get_clauses()[0] == expected_clause

    def test_convert_filters(self):
        filters = Filters()
        filters.add_from_string(FilterCombiner.AND, "Title:The Title,ID:100")
        filters.add_from_string(
            FilterCombiner.OR,
            "Description:describingText,Gebied_UUID:202211111111000000000000000000000006",
        )

        result = convert_filters(filters)

        expected_query_part = (
            "( Title = ? AND ID = ? ) AND ( Description = ? OR Gebied_UUID = ? )"
        )
        assert result.query_part == expected_query_part
        assert result.parameters == [
            "The Title",
            "100",
            "describingText",
            "202211111111000000000000000000000006",
        ]

    def test_convert_empty_filters(self):
        filters = Filters()

        result = convert_filters(filters)

        assert result.query_part == ""
        assert result.parameters == []

    def test_filters_converter_result_has_data(self):
        result = FiltersConverterResult(
            query_part="Title = ?", parameters=["The Title"]
        )
        assert result.has_data() == True

        empty_result = FiltersConverterResult(query_part="", parameters=[])
        assert empty_result.has_data() == False
