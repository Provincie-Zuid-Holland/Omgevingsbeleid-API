import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.utils import table_to_dict
from app.dynamic.utils.filters import Filters
from app.dynamic.utils.pagination import Sort, SortedPagination, SortOrder
from app.extensions.lineage_resolvers.endpoints.edit_object_static import EndpointHandler as EditStaticEndpoint
from app.extensions.lineage_resolvers.endpoints.object_latest import ObjectLatestEndpoint
from app.extensions.lineage_resolvers.endpoints.object_version import ObjectVersionEndpoint
from app.extensions.lineage_resolvers.endpoints.valid_list_lineage_tree import ValidListLineageTreeEndpoint
from app.extensions.lineage_resolvers.endpoints.valid_list_lineages import ValidListLineagesEndpoint
from app.tests.fixtures import LocalTables
from app.tests.helpers import patch_multiple

from .fixtures import endpoint_object_latest  # noqa


class TestEditStaticRequest(BaseModel):
    Test_Field: Optional[str] = None


class TestLineageResolvers:
    """
    Integration test endpoints to ensure DB querys
    and (de)serializing is working as expected.
    """

    @pytest.fixture
    def populate_db(self, local_tables: LocalTables, db: Session, populate_users):
        self.now = datetime.now(timezone.utc)
        self.five_days_ago = self.now - timedelta(days=5)
        self.five_days_later = self.now + timedelta(days=5)
        self.non_valid = local_tables.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="ambitie-1",
            Modified_Date=self.now,
            Object_Type="ambitie",
            Object_ID=1,
            Start_Validity=self.five_days_later,
            End_Validity=None,
        )

        self.valid = local_tables.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="ambitie-2",
            Modified_Date=self.five_days_ago,
            Object_Type="ambitie",
            Object_ID=2,
            Start_Validity=self.five_days_ago,
            End_Validity=self.five_days_later,
        )

        self.valid_latest = local_tables.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="ambitie-2",
            Modified_Date=self.now,
            Object_Type="ambitie",
            Object_ID=2,
            Start_Validity=self.five_days_ago,
            End_Validity=self.five_days_later,
        )

        self.other_type = local_tables.ObjectsTable(
            UUID=uuid.uuid4(),
            Code="beleidskeuze-1",
            Modified_Date=self.now,
            Object_Type="beleidskeuze",
            Object_ID=1,
            Start_Validity=self.five_days_ago,
            End_Validity=None,
        )

        self.statics = [
            local_tables.ObjectStaticsTable(Object_Type="ambitie", Object_ID=1, Code="ambitie-1"),
            local_tables.ObjectStaticsTable(Object_Type="ambitie", Object_ID=2, Code="ambitie-2"),
            local_tables.ObjectStaticsTable(Object_Type="beleidskeuze", Object_ID=1, Code="beleidskeuze-1"),
        ]

        self.super_user = populate_users[0]
        try:
            db.add_all(self.statics)
            db.add_all([self.non_valid, self.valid, self.valid_latest, self.other_type])
            db.commit()
            yield
        except Exception:
            raise Exception("Invalid fixture data")

    def run_events_mock(self, table_rows, event_dispatcher):
        rows: List[dict] = [table_to_dict(o) for o in table_rows]
        return rows

    def test_valid_lineage_endpoint(
        self,
        db: Session,
        local_tables: LocalTables,
        mock_dispatcher,
        endpoint_valid_lineage: ValidListLineagesEndpoint,
        populate_db,
    ):
        # Setup endpoint
        base_path = "app.extensions.lineage_resolvers.endpoints.valid_list_lineages"
        mock_table = local_tables.ObjectsTable

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
                pagination=SortedPagination(sort=Sort("Title", SortOrder.ASC)),
            )

        assert response.total == 1
        assert getattr(response.results[0], "UUID") == self.valid_latest.UUID

    def test_valid_lineage_tree(
        self,
        db: Session,
        local_tables: LocalTables,
        mock_dispatcher,
        endpoint_lineage_tree: ValidListLineageTreeEndpoint,
        populate_db,
    ):
        # Setup endpoint
        TEST_LINEAGE = 2

        base_path = "app.extensions.lineage_resolvers.endpoints.valid_list_lineage_tree"
        mock_table = local_tables.ObjectsTable

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
                pagination=SortedPagination(sort=Sort("Title", SortOrder.ASC)),
            )

        assert response.total == 2
        response_uuids = set([r.UUID for r in response.results])
        expected_uuids = set([self.valid.UUID, self.valid_latest.UUID])
        assert response_uuids == expected_uuids

    def test_latest_objects(
        self,
        local_tables: LocalTables,
        mock_dispatcher,
        endpoint_object_latest: ObjectLatestEndpoint,
        populate_db,
        test_object_repository,
    ):
        TEST_LINEAGE = 2

        with patch_multiple(
            patch(
                f"app.dynamic.repository.object_repository.ObjectsTable",
                local_tables.ObjectsTable,
            ),
            patch(
                f"app.extensions.lineage_resolvers.endpoints.object_latest.ObjectLatestEndpoint._run_events",
                self.run_events_mock,
            ),
        ):
            response = endpoint_object_latest._handler(
                object_repository=test_object_repository,
                event_dispatcher=mock_dispatcher,
                lineage_id=TEST_LINEAGE,
            )

        assert response["UUID"] == self.valid_latest.UUID

    def test_latest_objects_no_lineage(
        self,
        local_tables: LocalTables,
        mock_dispatcher,
        endpoint_object_latest: ObjectLatestEndpoint,
        populate_db,
        test_object_repository,
    ):
        # Should not exist
        TEST_LINEAGE = 9999

        with patch_multiple(
            patch(
                f"app.dynamic.repository.object_repository.ObjectsTable",
                local_tables.ObjectsTable,
            ),
            patch(
                f"app.extensions.lineage_resolvers.endpoints.object_latest.ObjectLatestEndpoint._run_events",
                self.run_events_mock,
            ),
        ):
            with pytest.raises(ValueError, match="lineage_id does not exist"):
                endpoint_object_latest._handler(
                    object_repository=test_object_repository,
                    event_dispatcher=mock_dispatcher,
                    lineage_id=TEST_LINEAGE,
                )

    def test_object_version(
        self,
        local_tables: LocalTables,
        mock_dispatcher,
        endpoint_object_version: ObjectVersionEndpoint,
        populate_db,
        test_object_repository,
    ):
        TEST_UUID = self.valid.UUID

        with patch_multiple(
            patch(
                f"app.dynamic.repository.object_repository.ObjectsTable",
                local_tables.ObjectsTable,
            ),
            patch(
                f"app.extensions.lineage_resolvers.endpoints.object_version.ObjectVersionEndpoint._run_events",
                self.run_events_mock,
            ),
        ):
            response = endpoint_object_version._handler(
                object_repository=test_object_repository,
                event_dispatcher=mock_dispatcher,
                object_uuid=TEST_UUID,
            )

        assert response["UUID"] == TEST_UUID

    def test_object_version_wrong_uuid(
        self,
        local_tables: LocalTables,
        mock_dispatcher,
        endpoint_object_version: ObjectVersionEndpoint,
        populate_db,
        test_object_repository,
    ):
        TEST_UUID = uuid.uuid4()

        with patch_multiple(
            patch(
                f"app.dynamic.repository.object_repository.ObjectsTable",
                local_tables.ObjectsTable,
            ),
            patch(
                f"app.extensions.lineage_resolvers.endpoints.object_version.ObjectVersionEndpoint._run_events",
                self.run_events_mock,
            ),
        ):
            with pytest.raises(ValueError, match="object_uuid does not exist"):
                endpoint_object_version._handler(
                    object_repository=test_object_repository,
                    event_dispatcher=mock_dispatcher,
                    object_uuid=TEST_UUID,
                )

    def test_object_latest(
        self,
        local_tables: LocalTables,
        mock_dispatcher,
        endpoint_object_latest: ObjectLatestEndpoint,
        populate_db,
        test_object_repository,
    ):
        TEST_ID = self.valid.Object_ID

        with patch_multiple(
            patch(
                f"app.dynamic.repository.object_repository.ObjectsTable",
                local_tables.ObjectsTable,
            ),
            patch(
                f"app.extensions.lineage_resolvers.endpoints.object_latest.ObjectLatestEndpoint._run_events",
                self.run_events_mock,
            ),
        ):
            response = endpoint_object_latest._handler(
                object_repository=test_object_repository,
                event_dispatcher=mock_dispatcher,
                lineage_id=TEST_ID,
            )

        assert response["UUID"] == self.valid_latest.UUID

    def test_object_latest_wrong_uuid(
        self,
        local_tables: LocalTables,
        mock_dispatcher,
        endpoint_object_latest: ObjectLatestEndpoint,
        populate_db,
        test_object_repository,
    ):
        TEST_ID = 999

        with patch_multiple(
            patch(
                f"app.dynamic.repository.object_repository.ObjectsTable",
                local_tables.ObjectsTable,
            ),
            patch(
                f"app.extensions.lineage_resolvers.endpoints.object_latest.ObjectLatestEndpoint._run_events",
                self.run_events_mock,
            ),
        ):
            with pytest.raises(ValueError, match="lineage_id does not exist"):
                endpoint_object_latest._handler(
                    object_repository=test_object_repository,
                    event_dispatcher=mock_dispatcher,
                    lineage_id=TEST_ID,
                )

    def test_object_edit_static(
        self,
        local_tables: LocalTables,
        test_object_static_repository,
        populate_db,
        mock_converter,
        db: Session,
    ):
        TEST_LINEAGE = 2
        object_in = TestEditStaticRequest(Test_Field="New value")

        endpoint = EditStaticEndpoint(
            converter=mock_converter,
            object_config_id="ambitie",
            object_type="ambitie",
            result_type=MagicMock(),
            repository=test_object_static_repository,
            db=db,
            user=self.super_user,
            lineage_id=TEST_LINEAGE,
            object_in=object_in,
        )

        with patch(
            f"app.dynamic.repository.object_static_repository.ObjectStaticsTable",
            local_tables.ObjectStaticsTable,
        ):
            response = endpoint.handle()

        assert response.message == "OK"
        stmt = (
            select(local_tables.ObjectStaticsTable)
            .filter(local_tables.ObjectStaticsTable.Object_Type == "ambitie")
            .filter(local_tables.ObjectStaticsTable.Object_ID == TEST_LINEAGE)
        )
        latest_object = db.scalars(stmt).first()
        # ensure new value exists in record
        assert latest_object.Test_Field == "New value"

    def test_edit_no_changes(
        self,
        local_tables: LocalTables,
        test_object_repository,
        populate_db,
        mock_converter,
        db,
    ):
        TEST_LINEAGE = 2
        object_in = TestEditStaticRequest()
        endpoint = EditStaticEndpoint(
            converter=mock_converter,
            object_config_id="ambitie",
            object_type="ambitie",
            result_type=MagicMock(),
            repository=test_object_repository,
            db=db,
            user=local_tables.UsersTabel,
            lineage_id=TEST_LINEAGE,
            object_in=object_in,
        )

        with pytest.raises(HTTPException, match="Nothing to update"):
            endpoint.handle()
