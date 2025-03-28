from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.tests.fixture_factories import ObjectStaticsFixtureFactory, UserFixtureFactory

from .fixtures import ExtendedLocalTables, local_tables, relation_repository  # noqa


class TestAcknowledgedRelationsRepository:
    """
    Test query logic and from/to side mapping.
    """

    @pytest.fixture(autouse=True)
    def setup(self, db, local_tables, relation_repository):  # noqa
        # timestamps
        self.now = datetime.now(timezone.utc)
        self.five_days_ago = self.now - timedelta(days=5)
        self.five_days_later = self.now + timedelta(days=5)

        # Factory data
        self.user_factory = UserFixtureFactory(db)
        self.user_factory.populate_db()
        self.statics_factory = ObjectStaticsFixtureFactory(db)
        self.statics_factory.populate_db()

        self.super_user = self.user_factory.objects[0]
        self.ba_user = self.user_factory.objects[2]

        self.repository = relation_repository

        self.relation_1 = local_tables.AcknowledgedRelationsTable(
            Created_Date=self.now,
            Created_By_UUID=self.super_user.UUID,
            Modified_By_UUID=self.super_user.UUID,
            Requested_By_Code="beleidskeuze-1",
            From_Code="beleidskeuze-1",
            From_Acknowledged=self.now,
            From_Acknowledged_By_UUID=self.super_user.UUID,
            From_Explanation="python",
            To_Code="beleidskeuze-2",
            To_Acknowledged=None,
        )

        self.relation_acknowledged = local_tables.AcknowledgedRelationsTable(
            Created_Date=self.five_days_ago,
            Created_By_UUID=self.ba_user.UUID,
            Modified_By_UUID=self.ba_user.UUID,
            Requested_By_Code="beleidskeuze-3",
            From_Code="beleidskeuze-3",
            From_Acknowledged=self.five_days_ago,
            From_Acknowledged_By_UUID=self.ba_user.UUID,
            From_Explanation="python",
            To_Code="beleidskeuze-2",
            To_Acknowledged=self.now,
            To_Acknowledged_By_UUID=self.super_user.UUID,
            To_Explanation="nice",
        )

        db.add_all([self.relation_1, self.relation_acknowledged])
        db.commit()

    def test_get_by_codes(self, local_tables: ExtendedLocalTables):  # noqa
        """
        Ensure query retrieves same object from DB
        """
        result = self.repository.get_by_codes(
            code_a=self.relation_1.From_Code,
            code_b=self.relation_1.To_Code,
        )

        assert result is not None
        for column in result.__table__.columns:
            assert getattr(result, column.name) == getattr(self.relation_1, column.name)

    def test_get_by_codes_invalid(self, local_tables: ExtendedLocalTables):  # noqa
        result = self.repository.get_by_codes(code_a="ambitie-1", code_b="ambitie-5")
        assert result is None

    def test_get_with_filters_requested_by_me(self, local_tables: ExtendedLocalTables):  # noqa
        result = self.repository.get_with_filters(
            code=self.relation_1.From_Code,
            requested_by_me=True,
            acknowledged=None,
        )
        assert len(result) == 1

    def test_get_with_filters_requested_by_anyone(self, db, local_tables: ExtendedLocalTables):  # noqa
        # Add another relation with different requested_by_code
        extra_relation_dict = {
            column.name: getattr(self.relation_1, column.name) for column in self.relation_1.__table__.columns
        }
        extra_relation_dict["Requested_By_Code"] = "beleidskeuze-1"
        extra_relation_dict["From_Code"] = "beleidskeuze-1"
        extra_relation_dict["To_Code"] = "beleidskeuze-3"
        extra_relation = local_tables.AcknowledgedRelationsTable(**extra_relation_dict)
        db.add(extra_relation)
        db.commit()

        result = self.repository.get_with_filters(
            code=extra_relation.From_Code,
            requested_by_me=False,
            acknowledged=None,
        )

        # Ensure all matching codes found, also if
        # Requested_By_Code is different
        assert len(result) == 2

    def test_get_filters_acknowledged(self, db: Session, local_tables: ExtendedLocalTables):  # noqa
        result = self.repository.get_with_filters(
            code=self.relation_acknowledged.Requested_By_Code,
            requested_by_me=True,
            acknowledged=True,
        )

        # should find only acknowledged records
        assert len(result) == 1

    def test_get_filters_hide_denied(self, db: Session, local_tables: ExtendedLocalTables):  # noqa
        relation_denied = local_tables.AcknowledgedRelationsTable(
            Created_Date=self.five_days_ago,
            Created_By_UUID=self.ba_user.UUID,
            Modified_By_UUID=self.ba_user.UUID,
            Requested_By_Code="beleidskeuze-3",
            From_Code="beleidskeuze-3",
            From_Acknowledged=self.five_days_ago,
            From_Acknowledged_By_UUID=self.ba_user.UUID,
            From_Explanation="me",
            To_Code="beleidskeuze-1",
            To_Acknowledged=None,
            Denied=datetime.now(timezone.utc),
        )
        db.add(relation_denied)
        db.commit()

        result = self.repository.get_with_filters(
            code=self.relation_acknowledged.Requested_By_Code,
            requested_by_me=True,
            acknowledged=None,
            show_inactive=False,
        )
        assert len(result) == 1

    def test_get_filters_hide_deleted(self, db: Session, local_tables: ExtendedLocalTables):  # noqa
        relation_deleted = local_tables.AcknowledgedRelationsTable(
            Created_Date=self.five_days_ago,
            Created_By_UUID=self.ba_user.UUID,
            Modified_By_UUID=self.ba_user.UUID,
            Requested_By_Code="beleidskeuze-3",
            From_Code="beleidskeuze-3",
            From_Acknowledged=self.five_days_ago,
            From_Acknowledged_By_UUID=self.ba_user.UUID,
            From_Explanation="me",
            To_Code="beleidskeuze-1",
            To_Acknowledged=None,
            Deleted_At=datetime.now(timezone.utc),
        )
        db.add(relation_deleted)
        db.commit()

        result = self.repository.get_with_filters(
            code=self.relation_acknowledged.Requested_By_Code,
            requested_by_me=True,
            acknowledged=None,
            show_inactive=False,
        )
        assert len(result) == 1
