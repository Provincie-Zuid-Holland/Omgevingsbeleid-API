import pytest
import uuid
from unittest.mock import MagicMock, patch

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi.exceptions import HTTPException
from sqlalchemy import Engine, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from app.tests.helpers import LocalTables
from app.extensions.lineage_resolvers.endpoints.valid_list_lineages import (
    ValidListLineagesEndpoint,
)
from app.extensions.lineage_resolvers.endpoints.valid_list_lineage_tree import (
    ValidListLineageTreeEndpoint,
)

from app.extensions.lineage_resolvers.endpoints.object_latest import (
    ObjectLatestEndpoint,
)

from app.extensions.lineage_resolvers.endpoints.object_version import (
    ObjectVersionEndpoint,
)

from app.extensions.lineage_resolvers.endpoints.edit_object_static import (
    EndpointHandler as EditStaticEndpoint
)
from app.dynamic.config.models import Model
from app.dynamic.utils.filters import Filters
from app.dynamic.utils.pagination import Pagination
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.converter import (
    Converter,
    ObjectConverterData,
)
from app.dynamic.repository.object_repository import ObjectRepository
from app.dynamic.repository.object_static_repository import ObjectStaticRepository
from app.tests.helpers import patch_multiple
from app.tests.mock_classes import MockResponseModel
from app.core.utils import table_to_dict


class TestLineageResolvers:
    """
    Integration test endpoints to ensure DB querys
    and (de)serializing is working as expected.
    """

    @pytest.fixture
    def table_setup(db: Session, engine: Engine, local_tables: LocalTables):
        # Setup Test table
        class ObjectsTable(local_tables.Base):
            __tablename__ = "objects"
            __table_args__ = {"extend_existing": True}

            UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
            Code: Mapped[str] = mapped_column(
                String(35), ForeignKey("object_statics.Code")
            )
            Modified_Date: Mapped[datetime]
            Object_ID: Mapped[int]
            Object_Type: Mapped[str]
            Start_Validity: Mapped[datetime]
            End_Validity: Mapped[Optional[datetime]]

            object_statics: Mapped["ObjectStaticsTable"] = relationship()

        class ObjectStaticsTable(local_tables.Base):
            __tablename__ = "object_statics"
            __table_args__ = {"extend_existing": True}

            Object_Type: Mapped[str] = mapped_column(String(25))
            Object_ID: Mapped[int]
            Code: Mapped[str] = mapped_column(String(35), primary_key=True)
            Test_Field: Mapped[Optional[str]]

        local_tables.ObjectsTable = ObjectsTable
        local_tables.ObjectStaticsTable = ObjectStaticsTable

        # setup db
        local_tables.Base.metadata.drop_all(engine)
        local_tables.Base.metadata.create_all(engine)
        yield local_tables
        # teardown db
        local_tables.Base.metadata.drop_all(engine)

    @pytest.fixture
    def populate_db(self, table_setup, db: Session):
        self.now = datetime.now()
        self.five_days_ago = self.now - timedelta(days=5)
        self.five_days_later = self.now + timedelta(days=5)

        self.non_valid = table_setup.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="ambitie-1",
            Modified_Date=self.now,
            Object_Type="ambitie",
            Object_ID=1,
            Start_Validity=self.five_days_later,
            End_Validity=None,
        )

        self.valid = table_setup.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="ambitie-2",
            Modified_Date=self.five_days_ago,
            Object_Type="ambitie",
            Object_ID=2,
            Start_Validity=self.five_days_ago,
            End_Validity=self.five_days_later,
        )

        self.valid_v2 = table_setup.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="ambitie-2",
            Modified_Date=self.now,
            Object_Type="ambitie",
            Object_ID=2,
            Start_Validity=self.five_days_ago,
            End_Validity=self.five_days_later,
        )

        self.other_type = table_setup.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="beleidskeuze-1",
            Modified_Date=self.now,
            Object_Type="beleidskeuze",
            Object_ID=1,
            Start_Validity=self.five_days_ago,
            End_Validity=None,
        )

        self.statics = [
            table_setup.ObjectStaticsTable(
                Object_Type="ambitie", Object_ID=1, Code="ambitie-1"
            ),
            table_setup.ObjectStaticsTable(
                Object_Type="ambitie", Object_ID=2, Code="ambitie-2"
            ),
            table_setup.ObjectStaticsTable(
                Object_Type="beleidskeuze", Object_ID=1, Code="beleidskeuze-1"
            ),
        ]
        try:
            db.add_all(self.statics)
            db.add_all([self.non_valid, self.valid, self.valid_v2, self.other_type])
            db.commit()
            yield
        except Exception:
            raise Exception("Invalid fixture data")

    @pytest.fixture
    def mock_converter(self):
        basic_converter = ObjectConverterData(
            column_deserializers=dict(),
            field_serializers=dict(),
        )

        converter = Converter()
        converter._per_object_id["ambitie"] = basic_converter
        return converter

    @pytest.fixture
    def mock_dispatcher(self):
        event_dispatcher_mock = MagicMock(spec=EventDispatcher)
        return event_dispatcher_mock

    @pytest.fixture
    def test_object_repository(self, db: Session):
        return ObjectRepository(db=db)

    @pytest.fixture
    def test_object_static_repository(self, db: Session):
        return ObjectStaticRepository(db=db)

    @pytest.fixture
    def endpoint_valid_lineage(self, mock_converter):
        response_model = Model(
            id="mock_get", name="AmbitieGet", pydantic_model=MockResponseModel
        )

        return ValidListLineagesEndpoint(
            converter=mock_converter,
            endpoint_id="test_objects_endpoint",
            path="/ambitie/testpath",
            object_id="ambitie",
            object_type="ambitie",
            response_model=response_model,
            allowed_filter_columns=[],
        )

    @pytest.fixture
    def endpoint_lineage_tree(self, mock_converter):
        response_model = Model(
            id="mock_get", name="AmbitieGet", pydantic_model=MockResponseModel
        )

        return ValidListLineageTreeEndpoint(
            converter=mock_converter,
            endpoint_id="test_objects_endpoint",
            path="/ambitie/testpath",
            object_id="ambitie",
            object_type="ambitie",
            response_model=response_model,
            allowed_filter_columns=[],
        )

    @pytest.fixture
    def endpoint_object_latest(self, mock_converter):
        response_model = Model(
            id="mock_get", name="AmbitieGet", pydantic_model=MockResponseModel
        )

        return ObjectLatestEndpoint(
            converter=mock_converter,
            endpoint_id="test_objects_endpoint",
            path="/ambitie/testpath",
            object_id="ambitie",
            object_type="ambitie",
            response_model=response_model,
        )

    @pytest.fixture
    def endpoint_object_version(self, mock_converter):
        response_model = Model(
            id="mock_get", name="AmbitieGet", pydantic_model=MockResponseModel
        )
        return ObjectVersionEndpoint(
            converter=mock_converter,
            endpoint_id="test_objects_endpoint",
            path="/ambitie/testpath",
            object_id="ambitie",
            object_type="ambitie",
            response_model=response_model,
        )

    def run_events_mock(self, table_rows, event_dispatcher):
        rows: List[dict] = [table_to_dict(o) for o in table_rows]
        return rows

    def test_valid_lineage_endpoint(
        self,
        db: Session,
        table_setup: LocalTables,
        mock_dispatcher,
        endpoint_valid_lineage: ValidListLineagesEndpoint,
        populate_db,
    ):
        # Setup endpoint
        base_path = "app.extensions.lineage_resolvers.endpoints.valid_list_lineages"
        mock_table = table_setup.ObjectsTable

        with patch_multiple(
            patch(f"{base_path}.ObjectsTable", mock_table),
            patch(
                f"{base_path}.ValidListLineagesEndpoint._run_events",
                self.run_events_mock,
            ),
        ):
            response = endpoint_valid_lineage._handler(
                db=db,
                event_dispatcher=mock_dispatcher,
                filters=Filters(),
                pagination=Pagination(),
            )

        assert len(response) == 1
        assert response[0].UUID == self.valid_v2.UUID

    def test_valid_lineage_tree(
        self,
        db: Session,
        table_setup: LocalTables,
        mock_dispatcher,
        endpoint_lineage_tree: ValidListLineageTreeEndpoint,
        populate_db,
    ):
        # Setup endpoint
        TEST_LINEAGE = 2

        base_path = "app.extensions.lineage_resolvers.endpoints.valid_list_lineage_tree"
        mock_table = table_setup.ObjectsTable

        with patch_multiple(
            patch(f"{base_path}.ObjectsTable", mock_table),
            patch(
                f"{base_path}.ValidListLineageTreeEndpoint._run_events",
                self.run_events_mock,
            ),
        ):
            response = endpoint_lineage_tree._handler(
                db=db,
                event_dispatcher=mock_dispatcher,
                lineage_id=TEST_LINEAGE,
                filters=Filters(),
                pagination=Pagination(),
            )

        assert len(response) == 2
        response_uuids = set([r.UUID for r in response])
        expected_uuids = set([self.valid.UUID, self.valid_v2.UUID])
        assert response_uuids == expected_uuids

    def test_latest_objects(
        self,
        table_setup: LocalTables,
        mock_dispatcher,
        endpoint_object_latest: ObjectLatestEndpoint,
        populate_db,
        test_object_repository
    ):
        TEST_LINEAGE = 2

        with patch_multiple(
            patch(f"app.dynamic.repository.object_repository.ObjectsTable", table_setup.ObjectsTable),
            patch(f"app.extensions.lineage_resolvers.endpoints.object_latest.ObjectLatestEndpoint._run_events", self.run_events_mock)
        ):
            response = endpoint_object_latest._handler(
                object_repository=test_object_repository,
                event_dispatcher=mock_dispatcher,
                lineage_id=TEST_LINEAGE
            )

        assert response.UUID == self.valid_v2.UUID


    def test_latest_objects_no_lineage(
        self,
        table_setup: LocalTables,
        mock_dispatcher,
        endpoint_object_latest: ObjectLatestEndpoint,
        populate_db,
        test_object_repository
    ):
        # Should not exist
        TEST_LINEAGE = 9999

        with patch_multiple(
            patch(f"app.dynamic.repository.object_repository.ObjectsTable", table_setup.ObjectsTable),
            patch(f"app.extensions.lineage_resolvers.endpoints.object_latest.ObjectLatestEndpoint._run_events", self.run_events_mock)
        ):
            with pytest.raises(ValueError, match="lineage_id does not exist"):
                endpoint_object_latest._handler(
                    object_repository=test_object_repository,
                    event_dispatcher=mock_dispatcher,
                    lineage_id=TEST_LINEAGE
                )

    def test_object_version(
        self,
        table_setup: LocalTables,
        mock_dispatcher,
        endpoint_object_version: ObjectVersionEndpoint,
        populate_db,
        test_object_repository
    ):
        TEST_UUID = self.valid.UUID

        with patch_multiple(
            patch(f"app.dynamic.repository.object_repository.ObjectsTable", table_setup.ObjectsTable),
            patch(f"app.extensions.lineage_resolvers.endpoints.object_version.ObjectVersionEndpoint._run_events", self.run_events_mock)
        ):
            response = endpoint_object_version._handler(
                object_repository=object_repository,
                event_dispatcher=mock_dispatcher,
                object_uuid=TEST_UUID
            )

        assert response.UUID == self.valid_v2.UUID

    def test_object_version_wrong_uuid(
        self,
        table_setup: LocalTables,
        mock_dispatcher,
        endpoint_object_version: ObjectVersionEndpoint,
        populate_db,
        test_object_repository
    ):
        TEST_UUID = uuid.uuid4()

        with patch_multiple(
            patch(f"app.dynamic.repository.object_repository.ObjectsTable", table_setup.ObjectsTable),
            patch(f"app.extensions.lineage_resolvers.endpoints.object_version.ObjectVersionEndpoint._run_events", self.run_events_mock)
        ):
            with pytest.raises(ValueError, match="object_uuid does not exist"):
                endpoint_object_version._handler(
                    object_repository=test_object_repository,
                    event_dispatcher=mock_dispatcher,
                    object_uuid=TEST_UUID
                )

    def test_object_edit_static(
        self,
        table_setup: LocalTables,
        test_object_static_repository,
        populate_db,
        mock_converter,
        db
    ):
        TEST_LINEAGE = 2
        CHANGES = {
            "Test_Field": "New value"
        }
        endpoint = EditStaticEndpoint(
            converter=mock_converter,
            object_config_id="ambitie",
            object_type="ambitie",
            repository=test_object_static_repository,
            db=db,
            user=table_setup.UsersTabel,
            changes=CHANGES,
            lineage_id=TEST_LINEAGE
        )

        with patch_multiple(
            patch(f"app.dynamic.repository.object_repository.ObjectsTable", table_setup.ObjectsTable),
            patch(f"app.dynamic.repository.object_static_repository.ObjectStaticRepository", table_setup.ObjectStaticsTable),
        ):
            response = endpoint.handle()

        assert response.message == "OK"
        # Query specific row and assert the update values
        # db.query()
        # assert

    def test_edit_no_changes(
        self,
        table_setup: LocalTables,
        test_object_repository,
        populate_db,
        mock_converter,
        db
    ):
        TEST_LINEAGE = 2
        CHANGES = {}
        endpoint = EditStaticEndpoint(
            converter=mock_converter,
            object_config_id="ambitie",
            object_type="ambitie",
            repository=test_object_repository,
            db=db,
            user=table_setup.UsersTabel,
            changes=CHANGES,
            lineage_id=TEST_LINEAGE
        )

        with pytest.raises(HTTPException, match="Nothing to update"):
            endpoint.handle()

