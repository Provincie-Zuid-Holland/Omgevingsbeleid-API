from unittest.mock import MagicMock, call, patch

import pytest
from fastapi import FastAPI

from app.dynamic.config.models import Column
from app.dynamic.dynamic_app import DynamicApp, DynamicAppBuilder
from app.dynamic.generate_table import generate_table
from app.tests.conftest import TestSettings
from app.tests.helpers import patch_multiple
from app.tests.fixtures import FakeExtension, LocalTables


class TestDynamicAppBuilder:
    @pytest.fixture
    def builder(self):
        builder = DynamicAppBuilder(TestSettings.BASE_TEST_CONFIG_FILE)
        builder._load_yml = MagicMock(return_value={})
        return builder

    def test_register_extension(self, local_tables):  # noqa
        with patch_multiple(
            patch(
                "app.dynamic.db.objects_table.ObjectsTable", local_tables.ObjectsTable
            ),
            patch(
                "app.dynamic.db.object_static_table.ObjectStaticsTable",
                local_tables.ObjectStaticsTable,
            ),
        ):
            builder = DynamicAppBuilder(TestSettings.BASE_TEST_CONFIG_FILE)
            for ext in TestSettings.BASE_EXTENSIONS:
                builder.register_extension(ext)

            builder.register_objects(TestSettings.TEST_OBJECT_CONFIG_PATH)

            extension = FakeExtension()
            builder.register_extension(extension)
            builder.build()

            # Assert all extensions registers are called when building
            expected_calls = [
                "initialize",
                "register_listeners",
                "register_commands",
                "register_base_columns",
                "register_base_fields",
                "register_endpoint_resolvers",
                "register_event_dispatcher",
                "register_converter",
                "register_models_resolver",
                "register_tables",
                "register_models",
                "register_endpoints",
            ]
            for call_ in extension.calls:
                assert call_[0] in expected_calls

    def test_register_objects(self, builder, mocker):
        # Set up mock directory structure
        dir_path = TestSettings.TEST_OBJECT_CONFIG_PATH
        file_paths = [
            f"{dir_path}/file1.py",
            f"{dir_path}/_file2.py",
            f"{dir_path}/file_3.py",
        ]
        mocker.patch("os.listdir", return_value=["file1.py", "_file2.py", "file_3.py"])
        mocker.patch("os.path.isfile", lambda path: path in file_paths)

        builder.register_object = MagicMock()
        builder.register_objects(dir_path)

        # Assert that register_object is called with expected file paths
        # List of paths should mirror the files in test config folder
        expected_file_paths = [f"{dir_path}testitem.yml"]
        assert builder.register_object.call_args_list == [
            call(expected_file_path) for expected_file_path in expected_file_paths
        ]

    def test_register_object(self, builder):
        builder.register_object("test.yml")
        builder._load_yml.assert_called_once_with("test.yml")

    def test_generate_tables_base_col(self, local_tables: LocalTables, mock_dispatcher):
        int_col = Column(
            id="col1", name="intcolumn", type="int", nullable=False, static=False
        )
        varc_col = Column(
            id="col2", name="varcolumn", type="str", nullable=False, static=False
        )
        date_col = Column(
            id="col3",
            name="datecolumn",
            type="datetime",
            nullable=False,
            static=False,
        )
        static_col = Column(
            id="col4", name="imstatic", type="str", nullable=False, static=True
        )

        columns = {
            "col1": int_col,
            "col2": varc_col,
            "col3": date_col,
            "col4": static_col,
        }

        with patch(
            "app.dynamic.db.objects_table.ObjectsTable", local_tables.ObjectsTable
        ):
            generate_table(
                event_dispatcher=mock_dispatcher,
                table_type=local_tables.ObjectsTable,
                table_name="ObjectsTable",
                columns=columns,
                static=False,
            )

        assert hasattr(local_tables.ObjectsTable, "intcolumn")
        assert hasattr(local_tables.ObjectsTable, "varcolumn")
        assert hasattr(local_tables.ObjectsTable, "datecolumn")
        # Should not have static columns as it was called with static=False
        assert not hasattr(local_tables.ObjectsTable, "imstatic")
        # Assert no events fired as all columns are handled
        assert mock_dispatcher.dispatch.call_count == 0

    def test_generate_tables_unknown_type(
        self, local_tables: LocalTables, mock_dispatcher
    ):
        int_col = Column(
            id="col1", name="intcolumn", type="int", nullable=False, static=False
        )
        unknown_type = Column(
            id="col2",
            name="unknowncolumn",
            type="user_uuid",
            nullable=False,
            static=False,
        )
        columns = {"col1": int_col, "col2": unknown_type}

        with patch(
            "app.dynamic.db.objects_table.ObjectsTable", local_tables.ObjectsTable
        ):
            generate_table(
                event_dispatcher=mock_dispatcher,
                table_type=local_tables.ObjectsTable,
                table_name="ObjectsTable",
                columns=columns,
                static=False,
            )

        assert hasattr(local_tables.ObjectsTable, "intcolumn")
        assert not hasattr(local_tables.ObjectsTable, "unknowncolumn")

        # Assert event is fired as 1 column type was unknown
        assert mock_dispatcher.dispatch.call_count == 1

    def test_generate_tables_static_col(
        self, local_tables: LocalTables, mock_dispatcher
    ):
        int_col = Column(
            id="col1", name="intcolumn", type="int", nullable=False, static=False
        )
        static_col = Column(
            id="col2", name="imstatic", type="str", nullable=False, static=True
        )
        columns = {"col1": int_col, "col2": static_col}

        with patch_multiple(
            patch(
                "app.dynamic.db.objects_table.ObjectsTable", local_tables.ObjectsTable
            ),
            patch(
                "app.dynamic.db.object_static_table.ObjectStaticsTable",
                local_tables.ObjectStaticsTable,
            ),
        ):
            generate_table(
                event_dispatcher=mock_dispatcher,
                table_type=local_tables.ObjectStaticsTable,
                table_name="ObjectStaticsTable",
                columns=columns,
                static=True,
            )

        assert hasattr(local_tables.ObjectStaticsTable, "imstatic")
        assert not hasattr(local_tables.ObjectStaticsTable, "intcolumn")

        assert not hasattr(local_tables.ObjectsTable, "intcolumn")
        assert not hasattr(local_tables.ObjectsTable, "imstatic")

        assert mock_dispatcher.dispatch.call_count == 0


class TestDynamicApp:
    def test_run(self):
        app = FastAPI()
        dynamic_app = DynamicApp(app, MagicMock())
        assert dynamic_app.run() == app

    def test_run_commands(self):
        commands_mock = MagicMock()
        dynamic_app = DynamicApp(FastAPI(), commands_mock)
        dynamic_app.run_commands()
        commands_mock.assert_called_once()
