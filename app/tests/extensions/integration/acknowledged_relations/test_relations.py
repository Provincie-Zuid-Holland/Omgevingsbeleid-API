import pytest
from fastapi.exceptions import HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.extensions.acknowledged_relations.endpoints.request_acknowledged_relation import (
    EndpointHandler as RequestEndpoint,
    RequestAcknowledgedRelation,
)

from app.extensions.acknowledged_relations.endpoints.edit_acknowledged_relation import (
    EndpointHandler as EditEndpoint,
    EditAcknowledgedRelation,
)

from .fixtures import (
    local_tables,
    ExtendedLocalTables,
    relation_repository,
)  # noqa

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
            From_Acknowledged=1,
            From_Acknowledged_Date=self.now,
            From_Acknowledged_By_UUID=self.super_user.UUID,
            From_Title="monty",
            From_Explanation="python",
            To_Code="beleidskeuze-2",
            To_Acknowledged=0,
        )

    def test_request_new_relation(
        self, db: Session, local_tables: ExtendedLocalTables  # noqa
    ):
        """
        Create new request for acknowledged relation, ensure db state is as expected.
        - from bk1 -> to bk2
        """
        requesting_user = self.super_user
        request_obj = RequestAcknowledgedRelation(
            Object_ID=2, Object_Type="beleidskeuze", Title="monty", Explanation="python"
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
        assert relation.From_Acknowledged == 1
        assert relation.To_Acknowledged == 0
        assert relation.To_Acknowledged_Date is None
        assert relation.To_Acknowledged_By_UUID is None
        assert relation.To_Title == ""
        assert relation.To_Explanation == ""

    def test_request_invalid_object(
        self, db: Session, local_tables: ExtendedLocalTables  # noqa
    ):
        """
        Create new request for acknowledged relation, ensure db state is as expected.
        - from bk1 -> to bk2
        """
        requesting_user = self.super_user
        request_obj = RequestAcknowledgedRelation(
            Object_ID=1, Object_Type="beleidskeuze", Title="monty", Explanation="python"
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
        self, db: Session, local_tables: ExtendedLocalTables  # noqa
    ):
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
            Title="monty",
            Explanation="python",
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
        assert relation.From_Acknowledged == 1
        assert relation.From_Acknowledged_By_UUID == self.super_user.UUID
        assert relation.To_Acknowledged == 1
        assert relation.To_Acknowledged_By_UUID == self.ba_user.UUID
        assert relation.To_Title == "monty"
        assert relation.To_Explanation == "python"

    def test_edit_relation_not_found(
        self, db: Session, local_tables: ExtendedLocalTables  # noqa
    ):
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
