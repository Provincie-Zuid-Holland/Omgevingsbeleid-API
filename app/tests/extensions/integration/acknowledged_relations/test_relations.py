import pytest
from copy import deepcopy
from fastapi.exceptions import HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.extensions.acknowledged_relations.models.models import (
    EditAcknowledgedRelation,
    RequestAcknowledgedRelation,
)
from app.extensions.acknowledged_relations.endpoints.request_acknowledged_relation import (
    EndpointHandler as RequestEndpoint,
)

from app.extensions.acknowledged_relations.endpoints.edit_acknowledged_relation import (
    EndpointHandler as EditEndpoint,
)

from app.extensions.acknowledged_relations.endpoints.list_acknowledged_relations import (
    EndpointHandler as ListEndpoint,
)

from .fixtures import local_tables, ExtendedLocalTables, relation_repository  # noqa

from app.tests.fixture_factories import (
    UserFixtureFactory,
    ObjectStaticsFixtureFactory,
    ObjectFixtureFactory,
)


class TestAcknowledgedRelationsEndpoint:
    """
    Test handling the endpoint and building AcknowledgedRelation models
    """

    @pytest.fixture(autouse=True)
    def setup(self, db, local_tables, relation_repository):  # noqa
        # timestamps
        self.now = datetime.now()
        self.five_days_ago = self.now - timedelta(days=5)
        self.five_days_later = self.now + timedelta(days=5)

        # Factory data
        self.user_factory = UserFixtureFactory(db)
        self.user_factory.populate_db()
        self.statics_factory = ObjectStaticsFixtureFactory(db)
        self.statics_factory.populate_db()

        self.object_factory = ObjectFixtureFactory(db, local_tables)
        self.object_factory.create_all_objects()
        for obj in self.object_factory.objects:
            obj.Start_Validity = self.five_days_ago
            obj.End_Validity = self.five_days_later
        self.object_factory.populate_db()

        self.super_user = self.user_factory.objects[0]
        self.ba_user = self.user_factory.objects[2]

        self.repository = relation_repository
        self.relation_request = local_tables.AcknowledgedRelationsTable(
            Created_Date=self.now,
            Created_By_UUID=self.super_user.UUID,
            Modified_By_UUID=self.super_user.UUID,
            Requested_By_Code="beleidskeuze-1",
            From_Code="beleidskeuze-1",
            From_Acknowledged=self.now,
            From_Acknowledged_By_UUID=self.super_user.UUID,
            From_Explanation="monty",
            To_Code="beleidskeuze-2",
            To_Acknowledged=None,
        )

    def test_request_new_relation(
        self, db: Session, local_tables: ExtendedLocalTables
    ):  # noqa
        """
        Create new request for acknowledged relation, ensure db state is as expected.
        - from bk1 -> to bk2
        """
        requesting_user = self.super_user
        request_obj = RequestAcknowledgedRelation(
            Object_ID=2, Object_Type="beleidskeuze", Explanation="python"
        )
        endpoint = RequestEndpoint(
            db=db,
            user=requesting_user,
            object_type="beleidskeuze",
            lineage_id=1,
            allowed_object_types=["beleidskeuze"],
            object_in=request_obj,
        )

        response = endpoint.handle()

        assert response.message == "OK"

        # Fetch result to verify state
        relation = self.repository.get_by_codes("beleidskeuze-2", "beleidskeuze-1")
        assert relation is not None

        # assert From side is acknowledged, to side is empty
        assert relation.From_Acknowledged != None
        assert relation.To_Acknowledged == None
        assert relation.To_Acknowledged_By_UUID is None
        assert relation.To_Explanation == ""

    def test_request_invalid_object(
        self, db: Session, local_tables: ExtendedLocalTables
    ):  # noqa
        requesting_user = self.super_user
        request_obj = RequestAcknowledgedRelation(
            Object_ID=1, Object_Type="beleidskeuze", Explanation="monty"
        )
        endpoint = RequestEndpoint(
            db=db,
            user=requesting_user,
            object_type="beleidskeuze",
            lineage_id=1,
            allowed_object_types=["wrong-type"],
            object_in=request_obj,
        )

        with pytest.raises(HTTPException, match="Invalid Object_Type"):
            endpoint.handle()

    def test_acknowledge_relation(
        self, db: Session, local_tables: ExtendedLocalTables
    ):  # noqa
        """
        Test that opened request can be acknowledged by another user:
        - From bk1 -> To bk2
        """
        # Create new relation request
        db.add(self.relation_request)
        db.commit()

        # Build request
        request_obj = EditAcknowledgedRelation(
            Object_ID=1,
            Object_Type="beleidskeuze",
            Explanation="monty",
            Acknowledged=True,
        )
        endpoint = EditEndpoint(
            db=db,
            repository=self.repository,
            user=self.ba_user,
            object_type="beleidskeuze",
            lineage_id=2,
            object_in=request_obj,
        )

        response = endpoint.handle()

        assert response.message == "OK"

        # Fetch result to verify state
        relation = self.repository.get_by_codes("beleidskeuze-2", "beleidskeuze-1")
        assert relation is not None

        # assert both sides acknowledged
        assert relation.Is_Acknowledged
        assert relation.From_Acknowledged_By_UUID == self.super_user.UUID
        assert relation.To_Acknowledged_By_UUID == self.ba_user.UUID
        assert relation.To_Explanation == "monty"

    def test_deny_relation_request(
        self, db: Session, local_tables: ExtendedLocalTables
    ):  # noqa
        # Create new relation request
        db.add(self.relation_request)
        db.commit()

        # Build request
        request_obj = EditAcknowledgedRelation(
            Object_ID=1,
            Object_Type="beleidskeuze",
            Denied=True,
        )
        endpoint = EditEndpoint(
            db=db,
            repository=self.repository,
            user=self.ba_user,
            object_type="beleidskeuze",
            lineage_id=2,
            object_in=request_obj,
        )

        response = endpoint.handle()

        assert response.message == "OK"

        query = (
            db.query(local_tables.AcknowledgedRelationsTable)
            .filter(local_tables.AcknowledgedRelationsTable.From_Code == "beleidskeuze-1")
            .filter(local_tables.AcknowledgedRelationsTable.To_Code == "beleidskeuze-2")
        )
        relation = query.one()
        assert relation is not None
        assert relation.Is_Acknowledged is False
        assert relation.Denied is not None

    def test_cancel_relation_request(
        self, db: Session, local_tables: ExtendedLocalTables
    ):  # noqa
        """
        Test that a requested relation can be canceled using as soft delete
        """
        db.add(self.relation_request)
        db.commit()
        request_obj = EditAcknowledgedRelation(
            Object_ID=1,
            Object_Type="beleidskeuze",
            Deleted=True,
        )
        endpoint = EditEndpoint(
            db=db,
            repository=self.repository,
            user=self.ba_user,
            object_type="beleidskeuze",
            lineage_id=2,
            object_in=request_obj,
        )

        response = endpoint.handle()
        assert response.message == "OK"

        query = (
            db.query(local_tables.AcknowledgedRelationsTable)
            .filter(local_tables.AcknowledgedRelationsTable.From_Code == "beleidskeuze-1")
            .filter(local_tables.AcknowledgedRelationsTable.To_Code == "beleidskeuze-2")
        )
        relation = query.one()
        assert relation is not None
        assert relation.Deleted_At is not None
        assert relation.Is_Acknowledged is False
        assert relation.Denied is None

    def test_edit_relation_not_found(self, db: Session, local_tables: ExtendedLocalTables): # noqa
        request_obj = EditAcknowledgedRelation(
            Object_ID=999,
            Object_Type="beleidskeuze",
            Acknowledged=True,
        )
        endpoint = EditEndpoint(
            db=db,
            repository=self.repository,
            user=self.ba_user,
            object_type="beleidskeuze",
            lineage_id=998,
            object_in=request_obj,
        )

        with pytest.raises(HTTPException, match="Acknowledged relation not found"):
            endpoint.handle()

    def test_list_relations(self, db: Session, local_tables: ExtendedLocalTables):  # noqa
        # Create new relation request
        acknowledged = deepcopy(self.relation_request)
        acknowledged.Requested_By_Code = "beleidskeuze-3"
        acknowledged.From_Code = "beleidskeuze-3"
        acknowledged.To_Code = "beleidskeuze-1"
        acknowledged.To_Acknowledged = self.now
        acknowledged.To_Acknowledged_By_UUID = self.ba_user.UUID

        db.add(self.relation_request)
        db.add(acknowledged)
        db.commit()

        endpoint = ListEndpoint(
            repository=self.repository,
            object_code="beleidskeuze-1",
            requested_by_us=False,
            acknowledged=None,
            show_inactive=True
        )

        response = endpoint.handle()
        assert len(response) == 2 # show all
