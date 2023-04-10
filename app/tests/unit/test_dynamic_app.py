import pytest

from fastapi import FastAPI

from app.dynamic.dynamic_app import DynamicAppBuilder, DynamicApp

from app.tests.conftest import TestSettings
from app.tests.mock_classes import FakeExtension
from app.tests.helpers import TestDynamicApp, patch_multiple
from unittest.mock import MagicMock, call, patch


class TestDynamicAppBuilder:
    @pytest.fixture
    def builder(self):
        builder = DynamicAppBuilder(TestSettings.BASE_TEST_CONFIG_FILE)
        builder._load_yml = MagicMock(return_value={})
        return builder

    def test_register_extension(self, local_tables):
        # Setup mocks
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

        # Set up mocks and call register_objects
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

    # def test_generates_columns(self, local_tables: LocalTables):
    #     with patch_multiple(
    #         patch("app.core.db.base.Base", local_tables.Base),
    #         patch(
    #             "app.dynamic.db.objects_table.ObjectsTable", local_tables.ObjectsTable
    #         ),
    #     ):
    #         int_col = Column(
    #             id="col1", name="intcolumn", type="int", nullable=False, static=False
    #         )
    #         varc_col = Column(
    #             id="col1", name="varcolumn", type="int", nullable=False, static=False
    #         )
    #         columns = {"col1": int_col, "col2": varc_col}
    #         generate_dynamic_objects(columns)
    #         assert hasattr(local_tables.ObjectsTable, "intcolumn")
    #         assert hasattr(local_tables.ObjectsTable, "varcolumn")

    # def test_ignores_uuid_and_code(self, local_tables: LocalTables):
    #     with patch_multiple(
    #         patch("app.core.db.base.Base", local_tables.Base),
    #         patch(
    #             "app.dynamic.db.objects_table.ObjectsTable", local_tables.ObjectsTable
    #         ),
    #     ):
    #         columns = {
    #             "uuid": Column(
    #                 id="uuid",
    #                 name="uuid_columns",
    #                 type="int",
    #                 nullable=False,
    #                 static=False,
    #             ),
    #             "code": Column(
    #                 id="code",
    #                 name="code_column",
    #                 type="str",
    #                 nullable=True,
    #                 static=True,
    #             ),
    #             "testcol": Column(
    #                 id="testcol",
    #                 name="test_column",
    #                 type="str",
    #                 nullable=False,
    #                 static=False,
    #             ),
    #         }
    #         generate_dynamic_objects(columns)
    #         assert not hasattr(local_tables.ObjectsTable, "uuid_column")
    #         assert not hasattr(local_tables.ObjectsTable, "code_column")
    #         assert hasattr(local_tables.ObjectsTable, "test_column")

    # def test_ignores_static_columns(self, local_tables: LocalTables):
    #     with patch_multiple(
    #         patch("app.core.db.base.Base", local_tables.Base),
    #         patch(
    #             "app.dynamic.db.objects_table.ObjectsTable", local_tables.ObjectsTable
    #         ),
    #     ):
    #         columns = {
    #             "validcol": Column(
    #                 id="varchar_col",
    #                 name="varchar_col",
    #                 type="str",
    #                 nullable=False,
    #                 static=False,
    #             ),
    #             "testcol": Column(
    #                 id="static_col",
    #                 name="static_col",
    #                 type="int",
    #                 nullable=False,
    #                 static=True,
    #             ),
    #         }
    #         generate_dynamic_objects(columns)
    #         assert hasattr(local_tables.ObjectsTable, "varchar_col")
    #         assert not hasattr(local_tables.ObjectsTable, "static_col")

    # def test_raises_error_for_invalid_type(self, local_tables: LocalTables):
    #     with patch_multiple(
    #         patch("app.core.db.base.Base", local_tables.Base),
    #         patch(
    #             "app.dynamic.db.objects_table.ObjectsTable", local_tables.ObjectsTable
    #         ),
    #     ):
    #         varc_col = Column(
    #             id="col1", name="valid_type", type="str", nullable=False, static=False
    #         )
    #         invalid_col = Column(
    #             id="col2",
    #             name="intcolumn",
    #             type="invalid_type",
    #             nullable=False,
    #             static=False,
    #         )

    #         columns = {
    #             "validcol": varc_col,
    #             "testcol": invalid_col,
    #         }

    #         with pytest.raises(RuntimeError):
    #             generate_dynamic_objects(columns)


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
