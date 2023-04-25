import pytest
from app.dynamic.config.models import Column
from app.dynamic.config.loader.columns import columns_loader


class TestColumnLoader:
    @pytest.fixture
    def base_columns(self):
        return {
            "column1": Column(
                id="column1",
                name="Column 1",
                type="str",
                nullable=True,
            )
        }

    def test_columns_loader_adds_columns(self, base_columns):
        config = {"column2": {"name": "Column 2", "type": "int"}}
        result = columns_loader(base_columns, config)
        assert len(result) == 2
        assert "column2" in result
        assert result["column2"].name == "Column 2"
        assert result["column2"].type == "int"

    def test_columns_loader_raises_exception_for_existing_column(self, base_columns):
        config = {"column1": {"name": "Column 1", "type": "str"}}
        with pytest.raises(RuntimeError):
            columns_loader(base_columns, config)

    def test_columns_loader_default_values(self, base_columns):
        config = {"column2": {"name": "Column 2", "type": "int"}}

        result = columns_loader(base_columns, config)
        assert result["column2"].name == "Column 2"
        assert result["column2"].type == "int"
        assert result["column2"].nullable is False
        assert result["column2"].static is False
        assert len(result["column2"].serializers) == 0
        assert len(result["column2"].deserializers) == 0

    def test_columns_loader_nullable(self, base_columns):
        config = {"column2": {"name": "Column 2", "type": "int"}}

        result = columns_loader(base_columns, config)
        assert result["column2"].name == "Column 2"
        assert result["column2"].type == "int"
        assert result["column2"].nullable is False
        assert result["column2"].static is False
        assert len(result["column2"].serializers) == 0
        assert len(result["column2"].deserializers) == 0
