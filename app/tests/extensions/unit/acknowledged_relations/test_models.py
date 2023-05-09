import pytest
from datetime import datetime
from uuid import uuid4
from app.extensions.acknowledged_relations.models.models import (
    AcknowledgedRelation,
    AcknowledgedRelationSide,
)


class TestAcknowledgedRelationsSide:
    def test_relation_side_code(self):
        side_a = AcknowledgedRelationSide(
            Object_ID=1,
            Object_Type="beleidskeuze",
            Title="side_a title",
            Explanation="side_a expl",
        )

        assert side_a.Is_Acknowledged is False
        assert side_a.Code == "beleidskeuze-1"

    def test_relation_side_date(self):
        side_a = AcknowledgedRelationSide(
            Object_ID=1,
            Object_Type="beleidskeuze",
            Acknowledged=datetime.now(),
            Title="side_a title",
            Explanation="side_a expl",
        )

        assert side_a.Is_Acknowledged is True
        assert type(side_a.Acknowledged_Date) is datetime

    def test_relation_side_approve(self):
        side_a = AcknowledgedRelationSide(
            Object_ID=1,
            Object_Type="beleidskeuze",
            Title="side_a title",
            Explanation="side_a expl",
        )

        assert side_a.Is_Acknowledged is False
        assert side_a.Acknowledged_Date is None

        user_uuid = uuid4()
        now = datetime.now()
        side_a.approve(user_uuid, now)

        assert side_a.Is_Acknowledged is True
        assert side_a.Acknowledged_Date is now
        assert type(side_a.Acknowledged_Date) is datetime


class TestAcknowledgedRelation:
    @pytest.fixture
    def base_relation(self):
        side_a = AcknowledgedRelationSide(
            Object_ID=1,
            Object_Type="beleidskeuze",
            Title="side_a title",
            Explanation="side_a expl",
        )

        side_b = AcknowledgedRelationSide(
            Object_ID=2,
            Object_Type="beleidskeuze",
            Title="side_b title",
            Explanation="side_b expl",
        )

        user_uuid = uuid4()

        return AcknowledgedRelation(
            Side_A=side_a,
            Side_B=side_b,
            Requested_By_Code=side_a.Code,
            Created_By_UUID=user_uuid,
            Created_Date=datetime.now(),
            Modified_By_UUID=user_uuid,
            Modified_Date=datetime.now(),
        )

    def test_relation_approved(self, base_relation):
        relation = base_relation
        user_uuid = relation.Created_By_UUID

        assert relation.Is_Acknowledged is False

        relation.Side_A.approve(user_uuid)
        relation.Side_B.approve(user_uuid)

        assert relation.Is_Acknowledged is True

    def test_relation_deny(self, base_relation):
        relation = base_relation
        user_uuid = relation.Created_By_UUID

        assert relation.Is_Acknowledged is False
        relation.Side_A.approve(user_uuid)
        relation.Side_B.approve(user_uuid)
        assert relation.Is_Acknowledged is True

        relation.Denied = datetime.now()

        assert relation.Is_Acknowledged is False
        assert relation.Is_Denied is True
